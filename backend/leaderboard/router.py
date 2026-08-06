"""Leaderboard API endpoints.

Provides the GET /api/leaderboard endpoint with scope-based filtering
using Redis sorted sets for today/week/alltime and PostgreSQL for friends.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

from datetime import date, datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from auth.middleware import get_current_user, get_optional_user
from config import settings
from database import get_session
from leaderboard.category_leaderboard import (
    CategoryScope,
    get_category_leaderboard,
)
from models import Friendship, Ranking, User
from schemas import (
    CategoryLeaderboardResponse,
    LeaderboardEntry,
    LeaderboardResponse,
)

router = APIRouter(prefix="/api", tags=["leaderboard"])

LeaderboardScope = Literal["today", "week", "alltime", "friends"]


async def get_redis_client() -> redis.Redis:
    """FastAPI dependency that yields an async Redis client."""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def _get_today_key() -> str:
    """Get the Redis sorted set key for today's leaderboard."""
    today = date.today().isoformat()
    return f"leaderboard:today:{today}"


def _get_week_key() -> str:
    """Get the Redis sorted set key for this week's leaderboard."""
    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    return f"leaderboard:week:{iso_year}-W{iso_week:02d}"


ALLTIME_KEY = "leaderboard:alltime"


async def update_leaderboard_scores(
    user_id: UUID,
    score: float,
    redis_client: redis.Redis,
) -> None:
    """Update leaderboard sorted sets after a ranking submission.

    Increments the user's score in today, week, and all-time leaderboards.
    Score is added (accumulated) using ZINCRBY.

    Requirements: 12.3
    """
    user_id_str = str(user_id)
    today_key = _get_today_key()
    week_key = _get_week_key()

    # Increment scores in all scopes
    pipe = redis_client.pipeline()
    pipe.zincrby(today_key, score, user_id_str)
    pipe.zincrby(week_key, score, user_id_str)
    pipe.zincrby(ALLTIME_KEY, score, user_id_str)

    # Set TTLs for time-scoped leaderboards
    # Today's leaderboard expires at the end of the day (max 48h for safety)
    pipe.expire(today_key, 172800)
    # Week's leaderboard expires after 8 days
    pipe.expire(week_key, 691200)

    await pipe.execute()


def _compute_score_from_grade(letter_grade: str) -> float:
    """Convert a letter grade to a numeric score for leaderboard ranking.

    Higher grades earn more points:
    S=10, A=8, B=6, C=4, D=2
    """
    grade_scores = {"S": 10.0, "A": 8.0, "B": 6.0, "C": 4.0, "D": 2.0}
    return grade_scores.get(letter_grade, 2.0)


async def _get_redis_leaderboard(
    redis_client: redis.Redis,
    key: str,
    session: AsyncSession,
    limit: int = 50,
) -> list[LeaderboardEntry]:
    """Fetch leaderboard entries from a Redis sorted set.

    Returns entries sorted by score descending with user metadata
    from PostgreSQL.
    """
    # Get top entries from Redis sorted set (descending by score)
    entries = await redis_client.zrevrange(key, 0, limit - 1, withscores=True)

    if not entries:
        return []

    # Fetch user data for all user IDs
    user_ids = [UUID(user_id_str) for user_id_str, _ in entries]
    result = await session.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users_by_id = {user.id: user for user in result.scalars().all()}

    leaderboard_entries = []
    for rank_idx, (user_id_str, score) in enumerate(entries, start=1):
        user_id = UUID(user_id_str)
        user = users_by_id.get(user_id)
        if user is None:
            continue

        leaderboard_entries.append(
            LeaderboardEntry(
                rank=rank_idx,
                user_id=user_id,
                username=user.username,
                score=score,
                current_streak=user.current_streak,
            )
        )

    return leaderboard_entries


async def _get_friends_leaderboard(
    current_user: User,
    session: AsyncSession,
    redis_client: redis.Redis,
) -> list[LeaderboardEntry]:
    """Get leaderboard filtered to only the current user's friends.

    Uses the friendships table to determine friends, then retrieves
    their all-time scores from Redis and sorts by score descending.

    Requirements: 12.4
    """
    # Get friend IDs
    result = await session.execute(
        select(Friendship.friend_id).where(
            Friendship.user_id == current_user.id
        )
    )
    friend_ids = [row[0] for row in result.fetchall()]

    if not friend_ids:
        return []

    # Include the current user in the friends leaderboard
    all_ids = friend_ids + [current_user.id]

    # Get scores from the all-time leaderboard for these users
    scores: list[tuple[UUID, float]] = []
    for user_id in all_ids:
        score = await redis_client.zscore(ALLTIME_KEY, str(user_id))
        if score is not None:
            scores.append((user_id, score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Fetch user data
    user_ids_with_scores = [uid for uid, _ in scores]
    if not user_ids_with_scores:
        return []

    result = await session.execute(
        select(User).where(User.id.in_(user_ids_with_scores))
    )
    users_by_id = {user.id: user for user in result.scalars().all()}

    entries = []
    for rank_idx, (user_id, score) in enumerate(scores, start=1):
        user = users_by_id.get(user_id)
        if user is None:
            continue

        entries.append(
            LeaderboardEntry(
                rank=rank_idx,
                user_id=user_id,
                username=user.username,
                score=score,
                current_streak=user.current_streak,
            )
        )

    return entries


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    scope: LeaderboardScope = Query(default="today", description="Leaderboard scope"),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)] = None,
) -> LeaderboardResponse:
    """Get leaderboard entries for the specified scope.

    Supports today, week, alltime, and friends scopes.
    The friends scope requires authentication.

    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """
    if scope == "friends":
        if current_user is None:
            return LeaderboardResponse(scope=scope, entries=[])
        entries = await _get_friends_leaderboard(
            current_user, session, redis_client
        )
    elif scope == "today":
        key = _get_today_key()
        entries = await _get_redis_leaderboard(redis_client, key, session)
    elif scope == "week":
        key = _get_week_key()
        entries = await _get_redis_leaderboard(redis_client, key, session)
    else:  # alltime
        entries = await _get_redis_leaderboard(
            redis_client, ALLTIME_KEY, session
        )

    return LeaderboardResponse(scope=scope, entries=entries)


@router.get("/leaderboard/category", response_model=CategoryLeaderboardResponse)
async def get_category_leaderboard_endpoint(
    value: str = Query(..., description="Category value to get leaderboard for"),
    scope: CategoryScope = Query(default="today", description="Leaderboard scope: today, week, alltime"),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)] = None,
) -> CategoryLeaderboardResponse:
    """Get top 50 leaderboard entries for a specific category_value.

    Returns entries with rank, username, score, and date for the
    specified time scope.

    Requirements: 6.2, 6.3, 6.4
    """
    entries = await get_category_leaderboard(
        category_value=value,
        scope=scope,
        redis_client=redis_client,
        session=session,
    )

    return CategoryLeaderboardResponse(
        category_value=value,
        scope=scope,
        entries=entries,
    )
