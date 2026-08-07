"""Rankings API endpoints.

Provides endpoints for submitting rankings, retrieving ranking results
with full reveal data including consensus, community heatmap, and
controversial pick identification.
"""

from datetime import date, timezone as tz
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from auth.middleware import get_current_user, get_optional_user
from config import settings
from database import get_session
from models import (
    CommunityAggregate,
    Player,
    Ranking,
    Roll,
    RollPlayer,
    User,
)
from schemas import (
    CommunityHeatmapResponse,
    ControversialPickResponse,
    RankingResponse,
    RankingSubmitRequest,
    RevealResponse,
)
from scoring import (
    compute_analytics_consensus,
    compute_reputation_consensus,
    kendall_tau_distance,
    letter_grade,
)
from streak.logic import update_streak
from leaderboard.router import update_leaderboard_scores, _compute_score_from_grade
from leaderboard.category_leaderboard import update_category_leaderboard

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


async def get_redis_client() -> redis.Redis:
    """FastAPI dependency that yields an async Redis client."""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def _generate_commentary(grade: str) -> str:
    """Generate a one-line commentary based on the letter grade."""
    commentaries = {
        "S": "Perfect score! You and the data are in complete agreement.",
        "A": "Near perfect — you clearly know your hoops.",
        "B": "Solid ranking. A few debatable picks, but who doesn't have those?",
        "C": "Some hot takes in there. The data disagrees with a few of your calls.",
        "D": "Bold choices! The data says otherwise, but maybe you see something it doesn't.",
    }
    return commentaries.get(grade, "Interesting ranking!")


async def _get_roll_players(
    roll_id: int, session: AsyncSession
) -> list[dict]:
    """Fetch the players associated with a Roll, returning dicts for consensus computation."""
    result = await session.execute(
        select(Player)
        .join(RollPlayer, RollPlayer.player_id == Player.id)
        .where(RollPlayer.roll_id == roll_id)
    )
    players = result.scalars().all()

    player_dicts = []
    for p in players:
        player_dicts.append({
            "id": p.id,
            "name": p.name,
            "position": p.position,
            "era": p.era,
            "career_stats": p.career_stats or {},
            "peak_stats": p.peak_stats or {},
            "playoff_stats": p.playoff_stats or {},
            "all_nba_selections": p.all_nba_selections,
            "mvp_vote_shares": p.mvp_vote_shares,
            "championships": p.championships,
            "all_star_selections": p.all_star_selections,
            "hof_rank": p.hof_rank,
        })

    return player_dicts


async def _compute_community_heatmap(
    roll_id: int, session: AsyncSession
) -> CommunityHeatmapResponse:
    """Compute the community heatmap for a given Roll."""
    result = await session.execute(
        select(CommunityAggregate).where(CommunityAggregate.roll_id == roll_id)
    )
    aggregates = result.scalars().all()

    if not aggregates:
        return CommunityHeatmapResponse(data={}, total_submissions=0)

    # Calculate total submissions (sum of counts for slot 1 for any player,
    # since each submission contributes exactly one entry per slot)
    total_result = await session.execute(
        select(func.sum(CommunityAggregate.count))
        .where(CommunityAggregate.roll_id == roll_id)
        .where(CommunityAggregate.slot_position == 1)
    )
    total_submissions = total_result.scalar() or 0

    # Build heatmap: player_id -> slot -> percentage
    data: dict[int, dict[int, float]] = {}
    for agg in aggregates:
        if agg.player_id not in data:
            data[agg.player_id] = {}
        if total_submissions > 0:
            percentage = round((agg.count / total_submissions) * 100, 1)
        else:
            percentage = 0.0
        data[agg.player_id][agg.slot_position] = percentage

    return CommunityHeatmapResponse(
        data=data, total_submissions=total_submissions
    )


def _identify_controversial_pick(
    player_order: list[int], heatmap: CommunityHeatmapResponse
) -> ControversialPickResponse | None:
    """Identify the most controversial pick in the user's ranking.

    The controversial pick is the player-slot combination with the lowest
    community agreement percentage.
    """
    if not heatmap.data or heatmap.total_submissions == 0:
        return None

    min_agreement = float("inf")
    controversial_player_id = None
    controversial_slot = None

    for slot_idx, player_id in enumerate(player_order, start=1):
        player_data = heatmap.data.get(player_id, {})
        agreement = player_data.get(slot_idx, 0.0)

        if agreement < min_agreement:
            min_agreement = agreement
            controversial_player_id = player_id
            controversial_slot = slot_idx

    if controversial_player_id is None:
        return None

    return ControversialPickResponse(
        player_id=controversial_player_id,
        slot=controversial_slot,
        community_agreement=min_agreement,
    )


async def _update_community_aggregates(
    roll_id: int,
    player_order: list[int],
    session: AsyncSession,
    redis_client: redis.Redis,
) -> None:
    """Update community aggregate data for a ranking submission.

    Increments counts in the CommunityAggregate table and updates
    the Redis hash for near-real-time access.
    """
    for slot_idx, player_id in enumerate(player_order, start=1):
        # Upsert community aggregate in PostgreSQL
        result = await session.execute(
            select(CommunityAggregate).where(
                CommunityAggregate.roll_id == roll_id,
                CommunityAggregate.player_id == player_id,
                CommunityAggregate.slot_position == slot_idx,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.count += 1
        else:
            new_agg = CommunityAggregate(
                roll_id=roll_id,
                player_id=player_id,
                slot_position=slot_idx,
                count=1,
            )
            session.add(new_agg)

        # Update Redis hash for near-real-time access
        redis_key = f"community:{roll_id}"
        field = f"{player_id}:{slot_idx}"
        await redis_client.hincrby(redis_key, field, 1)

    # Set TTL on the Redis hash (24 hours) if it's a new key
    await redis_client.expire(f"community:{roll_id}", 86400)


@router.post("", response_model=RankingResponse, status_code=status.HTTP_201_CREATED)
async def submit_ranking(
    request: RankingSubmitRequest,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
) -> Ranking:
    """Submit a ranking for scoring.

    Authentication is optional. If authenticated, the ranking is associated
    with the user and updates leaderboards/streaks. If not authenticated,
    the ranking is stored anonymously (no leaderboard/streak updates).

    Validates the ranking is an exact permutation of the Roll's player set,
    computes the consensus ranking based on the selected rubric, calculates
    Kendall tau distance, assigns a letter grade, stores the ranking, and
    updates community aggregates.

    Returns 409 if an authenticated user has already submitted a ranking for this Roll.
    """
    # Fetch the Roll
    roll_result = await session.execute(
        select(Roll).where(Roll.id == request.roll_id)
    )
    roll = roll_result.scalar_one_or_none()

    if roll is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roll not found",
        )

    # Check for duplicate submission only for authenticated users
    if current_user is not None:
        existing_result = await session.execute(
            select(Ranking).where(
                Ranking.user_id == current_user.id,
                Ranking.roll_id == request.roll_id,
            )
        )
        existing_ranking = existing_result.scalar_one_or_none()

        if existing_ranking is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already submitted a ranking for this roll",
            )

    # Get the Roll's player set
    roll_players_result = await session.execute(
        select(RollPlayer.player_id).where(RollPlayer.roll_id == request.roll_id)
    )
    valid_player_ids = set(row[0] for row in roll_players_result.fetchall())

    # Validate the submitted ranking is an exact permutation
    submitted_ids = set(request.player_order)
    if submitted_ids != valid_player_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ranking must contain exactly the players from the roll",
        )

    if len(request.player_order) != len(valid_player_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ranking must not contain duplicate player IDs",
        )

    # Fetch full player data for consensus computation
    player_dicts = await _get_roll_players(request.roll_id, session)

    # Compute consensus ranking based on selected rubric
    if request.rubric == "analytics":
        consensus_order = compute_analytics_consensus(
            player_dicts, roll.theme_modifier
        )
    else:
        consensus_order = compute_reputation_consensus(
            player_dicts, roll.theme_modifier
        )

    # Calculate Kendall tau distance and letter grade
    distance = kendall_tau_distance(request.player_order, consensus_order)
    grade = letter_grade(distance)

    # Store the ranking
    ranking = Ranking(
        user_id=current_user.id if current_user else None,
        roll_id=request.roll_id,
        rubric=request.rubric,
        player_order=request.player_order,
        kendall_tau_distance=distance,
        letter_grade=grade,
        mode=roll.mode,
    )
    session.add(ranking)

    # Update community aggregates
    await _update_community_aggregates(
        request.roll_id, request.player_order, session, redis_client
    )

    # Only update streak and leaderboard for authenticated users
    if current_user is not None:
        # Update streak if this is a daily challenge completion
        if roll.mode == "daily" and roll.daily_date is not None:
            update_streak(current_user, roll.daily_date)

        # Update leaderboard scores in Redis
        leaderboard_score = _compute_score_from_grade(grade)
        await update_leaderboard_scores(current_user.id, leaderboard_score, redis_client)

        # Update category leaderboard if this roll has a category_value
        if roll.category_value is not None:
            await update_category_leaderboard(
                current_user.id, roll.category_value, leaderboard_score, redis_client
            )

    await session.commit()
    await session.refresh(ranking)

    return ranking


@router.get("/{ranking_id}", response_model=RevealResponse)
async def get_ranking_reveal(
    ranking_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RevealResponse:
    """Get full reveal data for a ranking.

    Returns the ranking details, consensus order, community heatmap,
    controversial pick identification, and commentary. This endpoint
    is public so users can share reveal links.
    """
    # Fetch the ranking
    result = await session.execute(
        select(Ranking).where(Ranking.id == ranking_id)
    )
    ranking = result.scalar_one_or_none()

    if ranking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking not found",
        )

    # Fetch player data and compute consensus
    player_dicts = await _get_roll_players(ranking.roll_id, session)

    # Fetch the roll for theme_modifier
    roll_result = await session.execute(
        select(Roll).where(Roll.id == ranking.roll_id)
    )
    roll = roll_result.scalar_one_or_none()

    if ranking.rubric == "analytics":
        consensus_order = compute_analytics_consensus(
            player_dicts, roll.theme_modifier
        )
    else:
        consensus_order = compute_reputation_consensus(
            player_dicts, roll.theme_modifier
        )

    # Compute community heatmap
    heatmap = await _compute_community_heatmap(ranking.roll_id, session)

    # Identify controversial pick
    controversial_pick = _identify_controversial_pick(
        ranking.player_order, heatmap
    )

    # Generate commentary
    commentary = _generate_commentary(ranking.letter_grade)

    # Build ranking response
    ranking_response = RankingResponse(
        id=ranking.id,
        user_id=ranking.user_id,
        roll_id=ranking.roll_id,
        rubric=ranking.rubric,
        player_order=ranking.player_order,
        kendall_tau_distance=ranking.kendall_tau_distance,
        letter_grade=ranking.letter_grade,
        mode=ranking.mode,
        created_at=ranking.created_at,
    )

    return RevealResponse(
        ranking=ranking_response,
        consensus_order=consensus_order,
        community_heatmap=heatmap,
        controversial_pick=controversial_pick,
        commentary=commentary,
    )
