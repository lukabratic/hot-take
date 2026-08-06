"""Category leaderboard helpers using Redis sorted sets.

Provides functions to update and retrieve per-category leaderboards
keyed by category_value with today/week/alltime scopes.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from models import User
from schemas import CategoryLeaderboardEntry

CategoryScope = Literal["today", "week", "alltime"]

# TTLs match the existing leaderboard pattern
TODAY_TTL = 172800  # 48 hours
WEEK_TTL = 691200  # 8 days


def _get_category_today_key(category_value: str) -> str:
    """Get Redis key for today's category leaderboard."""
    today = date.today().isoformat()
    return f"cat_leaderboard:{category_value}:today:{today}"


def _get_category_week_key(category_value: str) -> str:
    """Get Redis key for this week's category leaderboard."""
    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    return f"cat_leaderboard:{category_value}:week:{iso_year}-W{iso_week:02d}"


def _get_category_alltime_key(category_value: str) -> str:
    """Get Redis key for all-time category leaderboard."""
    return f"cat_leaderboard:{category_value}:alltime"


async def update_category_leaderboard(
    user_id: UUID,
    category_value: str,
    score: float,
    redis_client: redis.Redis,
) -> None:
    """Update category leaderboard sorted sets after a ranking submission.

    Increments the user's score in today, week, and all-time category
    leaderboards using ZINCRBY. Sets appropriate TTLs on time-scoped keys.

    Requirements: 6.1
    """
    user_id_str = str(user_id)
    today_key = _get_category_today_key(category_value)
    week_key = _get_category_week_key(category_value)
    alltime_key = _get_category_alltime_key(category_value)

    pipe = redis_client.pipeline()
    pipe.zincrby(today_key, score, user_id_str)
    pipe.zincrby(week_key, score, user_id_str)
    pipe.zincrby(alltime_key, score, user_id_str)

    # Set TTLs for time-scoped leaderboards
    pipe.expire(today_key, TODAY_TTL)
    pipe.expire(week_key, WEEK_TTL)

    await pipe.execute()


async def get_category_leaderboard(
    category_value: str,
    scope: CategoryScope,
    redis_client: redis.Redis,
    session: AsyncSession,
    limit: int = 50,
) -> list[CategoryLeaderboardEntry]:
    """Fetch top entries from a category leaderboard.

    Returns entries sorted by score descending with user metadata
    from PostgreSQL, including rank, username, score, and date.

    Requirements: 6.2, 6.3, 6.4
    """
    # Determine the Redis key based on scope
    if scope == "today":
        key = _get_category_today_key(category_value)
    elif scope == "week":
        key = _get_category_week_key(category_value)
    else:
        key = _get_category_alltime_key(category_value)

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

    today_str = date.today().isoformat()

    leaderboard_entries = []
    for rank_idx, (user_id_str, score) in enumerate(entries, start=1):
        user_id = UUID(user_id_str)
        user = users_by_id.get(user_id)
        if user is None:
            continue

        leaderboard_entries.append(
            CategoryLeaderboardEntry(
                rank=rank_idx,
                user_id=user_id,
                username=user.username,
                score=score,
                date=today_str,
            )
        )

    return leaderboard_entries
