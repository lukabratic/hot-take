"""Debate mode API endpoints.

Provides endpoints for creating debate sessions, retrieving session state,
and submitting rankings within a debate. Two users share the same Roll and
compare their rankings head-to-head.
"""

import random
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from auth.middleware import get_current_user
from config import settings
from database import get_session
from models import (
    DebateSession,
    Player,
    Ranking,
    Roll,
    RollPlayer,
    User,
)
from schemas import (
    DebateCreateRequest,
    DebateSessionResponse,
    RankingResponse,
    RankingSubmitRequest,
    Rubric,
)
from scoring import (
    compute_analytics_consensus,
    compute_reputation_consensus,
    kendall_tau_distance,
    letter_grade,
)
from rolls.generator import generate_roll
from rolls.player_selection import select_players, POSITION_MAPPING

router = APIRouter(prefix="/api/debate", tags=["debate"])


async def get_redis_client() -> redis.Redis:
    """FastAPI dependency that yields an async Redis client."""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


class DebateCompareResponse:
    """Not used as Pydantic — built inline for flexibility."""
    pass


@router.post("", response_model=DebateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_debate_session(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DebateSession:
    """Create a new debate session with a generated Roll.

    Generates a random Roll, selects players, persists them, and creates
    a DebateSession with the creator. Returns the session with its shareable ID.
    """
    # Generate a random Roll for the debate
    roll_data = generate_roll()

    # Query players matching the roll's position
    position = roll_data["position"]
    valid_positions = POSITION_MAPPING.get(position)
    if valid_positions is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown position: {position}",
        )

    result = await session.execute(
        select(Player).where(Player.position.in_(valid_positions))
    )
    all_players = result.scalars().all()

    # Select 5-7 random players
    count = random.randint(5, 7)
    if len(all_players) < count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insufficient players for position '{position}': need {count}, found {len(all_players)}",
        )

    selected_players = random.sample(list(all_players), count)

    # Persist Roll record
    roll_record = Roll(
        position=roll_data["position"],
        theme_modifier=roll_data["theme_modifier"],
        mode="debate",
    )
    session.add(roll_record)
    await session.flush()

    # Persist RollPlayer records with random display order
    shuffled_indices = list(range(len(selected_players)))
    random.shuffle(shuffled_indices)

    for display_order, player in zip(shuffled_indices, selected_players):
        roll_player = RollPlayer(
            roll_id=roll_record.id,
            player_id=player.id,
            display_order=display_order,
        )
        session.add(roll_player)

    # Create the debate session
    debate_session = DebateSession(
        roll_id=roll_record.id,
        creator_id=current_user.id,
        status="waiting",
    )
    session.add(debate_session)

    await session.commit()
    await session.refresh(debate_session)

    return debate_session


@router.get("/{session_id}", response_model=DebateSessionResponse)
async def get_debate_session(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DebateSession:
    """Get the current state of a debate session.

    Returns the session metadata including status (waiting or complete),
    participants, and the associated Roll ID.
    """
    result = await session.execute(
        select(DebateSession).where(DebateSession.id == session_id)
    )
    debate = result.scalar_one_or_none()

    if debate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate session not found",
        )

    return debate


@router.get("/{session_id}/roll")
async def get_debate_roll(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get the Roll and players for a debate session.

    Returns the full Roll data with player information so both
    participants can rank the same set of players.
    """
    result = await session.execute(
        select(DebateSession).where(DebateSession.id == session_id)
    )
    debate = result.scalar_one_or_none()

    if debate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate session not found",
        )

    # Fetch the Roll
    roll_result = await session.execute(
        select(Roll).where(Roll.id == debate.roll_id)
    )
    roll = roll_result.scalar_one_or_none()

    # Fetch players in display order
    players_result = await session.execute(
        select(Player)
        .join(RollPlayer, RollPlayer.player_id == Player.id)
        .where(RollPlayer.roll_id == debate.roll_id)
        .order_by(RollPlayer.display_order)
    )
    players = players_result.scalars().all()

    return {
        "id": roll.id,
        "position": roll.position,
        "theme_modifier": roll.theme_modifier,
        "mode": "debate",
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
            }
            for p in players
        ],
    }


@router.post("/{session_id}/ranking", status_code=status.HTTP_201_CREATED)
async def submit_debate_ranking(
    session_id: UUID,
    request: RankingSubmitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Submit a ranking within a debate session.

    Both the creator and opponent can submit one ranking each. When both
    have submitted, the session status moves to 'complete'. Prevents
    re-submission after a participant has already ranked.

    Returns the submitted ranking with score details and, if both have
    submitted, the full comparison data.
    """
    # Fetch the debate session
    result = await session.execute(
        select(DebateSession).where(DebateSession.id == session_id)
    )
    debate = result.scalar_one_or_none()

    if debate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate session not found",
        )

    # Validate the roll_id matches the debate's roll
    if request.roll_id != debate.roll_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roll ID does not match this debate session",
        )

    # Determine participant role
    is_creator = current_user.id == debate.creator_id
    is_opponent = debate.opponent_id is not None and current_user.id == debate.opponent_id

    if not is_creator and debate.opponent_id is None:
        # This user becomes the opponent
        debate.opponent_id = current_user.id
        is_opponent = True
    elif not is_creator and not is_opponent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debate session already has two participants",
        )

    # Check if this user already submitted a ranking for this roll
    existing_result = await session.execute(
        select(Ranking).where(
            Ranking.user_id == current_user.id,
            Ranking.roll_id == debate.roll_id,
        )
    )
    existing_ranking = existing_result.scalar_one_or_none()

    if existing_ranking is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a ranking for this debate",
        )

    # Validate the submitted ranking is an exact permutation of the roll's players
    roll_players_result = await session.execute(
        select(RollPlayer.player_id).where(RollPlayer.roll_id == debate.roll_id)
    )
    valid_player_ids = set(row[0] for row in roll_players_result.fetchall())

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
    player_dicts = await _get_roll_players(debate.roll_id, session)

    # Fetch the Roll for theme_modifier
    roll_result = await session.execute(
        select(Roll).where(Roll.id == debate.roll_id)
    )
    roll = roll_result.scalar_one_or_none()

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
        user_id=current_user.id,
        roll_id=debate.roll_id,
        rubric=request.rubric,
        player_order=request.player_order,
        kendall_tau_distance=distance,
        letter_grade=grade,
        mode="debate",
    )
    session.add(ranking)

    # Check if both participants have now submitted
    # Count rankings for this roll from both participants
    other_user_id = debate.creator_id if is_opponent else debate.opponent_id
    if other_user_id is not None:
        other_result = await session.execute(
            select(Ranking).where(
                Ranking.user_id == other_user_id,
                Ranking.roll_id == debate.roll_id,
            )
        )
        other_ranking = other_result.scalar_one_or_none()

        if other_ranking is not None:
            # Both have submitted — mark complete
            debate.status = "complete"

    await session.commit()
    await session.refresh(ranking)

    return {
        "ranking": {
            "id": ranking.id,
            "user_id": str(ranking.user_id),
            "roll_id": ranking.roll_id,
            "rubric": ranking.rubric,
            "player_order": ranking.player_order,
            "kendall_tau_distance": ranking.kendall_tau_distance,
            "letter_grade": ranking.letter_grade,
            "mode": ranking.mode,
            "created_at": ranking.created_at.isoformat(),
        },
        "consensus_order": consensus_order,
        "session_status": debate.status,
    }


@router.get("/{session_id}/compare")
async def get_debate_comparison(
    session_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get the full comparison view for a completed debate session.

    Returns both participants' rankings side by side with their scores,
    the consensus ranking, and highlights of where they differ. Only
    available after both participants have submitted.
    """
    result = await session.execute(
        select(DebateSession).where(DebateSession.id == session_id)
    )
    debate = result.scalar_one_or_none()

    if debate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate session not found",
        )

    if debate.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debate is not yet complete. Waiting for both participants to submit.",
        )

    # Fetch both rankings
    creator_ranking_result = await session.execute(
        select(Ranking).where(
            Ranking.user_id == debate.creator_id,
            Ranking.roll_id == debate.roll_id,
        )
    )
    creator_ranking = creator_ranking_result.scalar_one_or_none()

    opponent_ranking_result = await session.execute(
        select(Ranking).where(
            Ranking.user_id == debate.opponent_id,
            Ranking.roll_id == debate.roll_id,
        )
    )
    opponent_ranking = opponent_ranking_result.scalar_one_or_none()

    if creator_ranking is None or opponent_ranking is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find rankings for both participants",
        )

    # Compute consensus
    player_dicts = await _get_roll_players(debate.roll_id, session)

    roll_result = await session.execute(
        select(Roll).where(Roll.id == debate.roll_id)
    )
    roll = roll_result.scalar_one_or_none()

    # Use the creator's rubric for the consensus (both may differ)
    # Show both scores against their own chosen rubric
    creator_consensus = (
        compute_analytics_consensus(player_dicts, roll.theme_modifier)
        if creator_ranking.rubric == "analytics"
        else compute_reputation_consensus(player_dicts, roll.theme_modifier)
    )
    opponent_consensus = (
        compute_analytics_consensus(player_dicts, roll.theme_modifier)
        if opponent_ranking.rubric == "analytics"
        else compute_reputation_consensus(player_dicts, roll.theme_modifier)
    )

    # Fetch creator and opponent usernames
    creator_result = await session.execute(
        select(User).where(User.id == debate.creator_id)
    )
    creator_user = creator_result.scalar_one_or_none()

    opponent_result = await session.execute(
        select(User).where(User.id == debate.opponent_id)
    )
    opponent_user = opponent_result.scalar_one_or_none()

    # Identify differences between the two rankings
    differences = []
    for i, (c_id, o_id) in enumerate(
        zip(creator_ranking.player_order, opponent_ranking.player_order)
    ):
        if c_id != o_id:
            differences.append(i + 1)  # 1-indexed slot

    # Fetch player names for display
    players_result = await session.execute(
        select(Player)
        .join(RollPlayer, RollPlayer.player_id == Player.id)
        .where(RollPlayer.roll_id == debate.roll_id)
    )
    players = players_result.scalars().all()
    player_names = {p.id: p.name for p in players}

    return {
        "session_id": str(debate.id),
        "status": debate.status,
        "roll": {
            "id": roll.id,
            "position": roll.position,
            "theme_modifier": roll.theme_modifier,
        },
        "creator": {
            "user_id": str(debate.creator_id),
            "username": creator_user.username if creator_user else "Unknown",
            "ranking": {
                "id": creator_ranking.id,
                "rubric": creator_ranking.rubric,
                "player_order": creator_ranking.player_order,
                "kendall_tau_distance": creator_ranking.kendall_tau_distance,
                "letter_grade": creator_ranking.letter_grade,
            },
            "consensus_order": creator_consensus,
        },
        "opponent": {
            "user_id": str(debate.opponent_id),
            "username": opponent_user.username if opponent_user else "Unknown",
            "ranking": {
                "id": opponent_ranking.id,
                "rubric": opponent_ranking.rubric,
                "player_order": opponent_ranking.player_order,
                "kendall_tau_distance": opponent_ranking.kendall_tau_distance,
                "letter_grade": opponent_ranking.letter_grade,
            },
            "consensus_order": opponent_consensus,
        },
        "differences": differences,
        "player_names": player_names,
    }


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
