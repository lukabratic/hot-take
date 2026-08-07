"""Roll API endpoints.

Provides endpoints for fetching the daily challenge and generating
Quick Play and HoopIQ rolls.
"""

import random
from datetime import date, timezone, datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from config import settings
from database import get_session
from models import Player, Roll, RollPlayer, Ranking, User
from schemas import RollHoopIQResponse, PlayerHoopIQResponse, PlayerStats
from .daily import get_daily_challenge
from .quickplay import generate_quickplay_roll
from .generator import generate_roll, THEME_MODIFIERS
from .player_selection import select_players, POSITION_MAPPING
from .category_selection import select_players_by_category, CATEGORY_FILTERS

router = APIRouter(prefix="/api", tags=["rolls"])


async def get_redis() -> redis.Redis:
    """FastAPI dependency that yields an async Redis client."""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def _get_user_id_from_header(authorization: str | None) -> str | None:
    """Extract user ID from Authorization header.

    This is a placeholder until the full Clerk JWT verification middleware
    is implemented (Task 7). For now it simply extracts the bearer token
    value as the user identifier.
    """
    if authorization is None:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


@router.get("/daily")
async def get_daily(
    authorization: str | None = Header(default=None),
    redis_client: redis.Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    """Get today's daily challenge Roll.

    Authentication is optional. Returns the same Roll for all users on
    the same calendar day (UTC), including selected players.
    If the user is authenticated and already submitted today, returns 409 with ranking ID.
    """
    from auth.middleware import _decode_clerk_jwt

    token = _get_user_id_from_header(authorization)
    clerk_id = None

    if token is not None:
        # Decode JWT to get actual clerk_id (sub claim)
        try:
            payload = await _decode_clerk_jwt(token)
            clerk_id = payload.get("sub")
        except Exception:
            clerk_id = None

    today = datetime.now(timezone.utc).date()
    roll = await get_daily_challenge(today, redis_client)

    # Check if we already have a persisted Roll for today
    existing_roll_result = await session.execute(
        select(Roll).where(Roll.daily_date == today, Roll.mode == "daily")
    )
    roll_record = existing_roll_result.scalar_one_or_none()

    if roll_record is None:
        # Select players and persist the Roll
        position = roll["position"]
        valid_positions = POSITION_MAPPING.get(position)
        if valid_positions is None:
            raise HTTPException(status_code=500, detail=f"Unknown position: {position}")

        result = await session.execute(
            select(Player).where(Player.position.in_(valid_positions))
        )
        all_players = result.scalars().all()

        count = min(5, len(all_players))
        if count < 5:
            raise HTTPException(status_code=500, detail="Insufficient players for roll")

        rng = random.Random(f"daily_players_{today.isoformat()}_{position}")
        selected_players = rng.sample(list(all_players), count)

        roll_record = Roll(
            position=roll["position"],
            theme_modifier=roll["theme_modifier"],
            daily_date=today,
            mode="daily",
        )
        session.add(roll_record)
        await session.flush()

        for idx, player in enumerate(selected_players):
            rp = RollPlayer(
                roll_id=roll_record.id,
                player_id=player.id,
                display_order=idx,
            )
            session.add(rp)

        await session.commit()
        await session.refresh(roll_record)
    else:
        # Load the already-selected players
        rp_result = await session.execute(
            select(Player)
            .join(RollPlayer, RollPlayer.player_id == Player.id)
            .where(RollPlayer.roll_id == roll_record.id)
            .order_by(RollPlayer.display_order)
        )
        selected_players = list(rp_result.scalars().all())

    # Check if this user already submitted for today's roll
    if roll_record is not None and clerk_id:
        user_result = await session.execute(
            select(User).where(User.clerk_id == clerk_id)
        )
        user = user_result.scalar_one_or_none()

        if user is not None:
            existing_ranking_result = await session.execute(
                select(Ranking).where(
                    Ranking.user_id == user.id,
                    Ranking.roll_id == roll_record.id,
                )
            )
            existing_ranking = existing_ranking_result.scalar_one_or_none()
            if existing_ranking is not None:
                raise HTTPException(
                    status_code=409,
                    detail={"message": "Already submitted", "ranking_id": existing_ranking.id},
                )

    return {
        "id": roll_record.id,
        "position": roll_record.position,
        "theme_modifier": roll_record.theme_modifier,
        "mode": "daily",
        "daily_date": today.isoformat(),
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
                "careerStats": p.career_stats,
                "peakStats": p.peak_stats,
                "playoffStats": p.playoff_stats,
                "allNbaSelections": p.all_nba_selections,
                "mvpVoteShares": p.mvp_vote_shares,
                "championships": p.championships,
                "allStarSelections": p.all_star_selections,
                "hofRank": p.hof_rank,
                "bbrefId": p.bbref_id,
                "team": p.team,
            }
            for p in selected_players
        ],
    }


@router.get("/quickplay")
async def get_quickplay(
    authorization: str | None = Header(default=None),
    category_type: str | None = None,
    category_value: str | None = None,
    redis_client: redis.Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    """Generate a Quick Play Roll.

    Authentication is optional. If authenticated, the roll will avoid
    duplicating the user's most recent 5 Quick Play rolls.

    When category_type and category_value are provided, players are
    selected from the filtered category pool instead of the default
    position-based selection.
    """
    user_id = _get_user_id_from_header(authorization)

    use_category = category_type is not None and category_value is not None

    if use_category:
        # Validate category_type
        if category_type not in CATEGORY_FILTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category_type '{category_type}'. Must be one of: {list(CATEGORY_FILTERS.keys())}",
            )

        # Query all players and use category-based selection
        result = await session.execute(select(Player))
        all_players = result.scalars().all()

        # Convert ORM objects to dicts for the category selection function
        player_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
                "team": p.team,
                "conference": p.conference,
                "career_stats": p.career_stats,
                "peak_stats": p.peak_stats,
                "playoff_stats": p.playoff_stats,
                "all_nba_selections": p.all_nba_selections,
                "mvp_vote_shares": p.mvp_vote_shares,
                "championships": p.championships,
                "all_star_selections": p.all_star_selections,
                "hof_rank": p.hof_rank,
                "bbref_id": p.bbref_id,
            }
            for p in all_players
        ]

        try:
            selected_dicts = select_players_by_category(
                category_type, category_value, player_dicts, count=5
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Map back to ORM player objects for consistent response building
        selected_ids = {d["id"] for d in selected_dicts}
        selected_players = [p for p in all_players if p.id in selected_ids]

        # Generate a random theme modifier to combine with the category
        theme_modifier = random.choice(THEME_MODIFIERS)

        # Use the category_type as the position field for compatibility,
        # or "Mixed" if category is not position-based
        if category_type == "position":
            roll_position = category_value
        else:
            roll_position = "Mixed"

    else:
        # Existing position-based behavior
        roll = await generate_quickplay_roll(user_id, redis_client)

        position = roll["position"]
        valid_positions = POSITION_MAPPING.get(position)
        if valid_positions is None:
            raise HTTPException(status_code=500, detail=f"Unknown position: {position}")

        result = await session.execute(
            select(Player).where(Player.position.in_(valid_positions))
        )
        all_players = result.scalars().all()

        count = 5
        if len(all_players) < count:
            count = len(all_players)
        if count < 5:
            raise HTTPException(status_code=500, detail="Insufficient players for roll")

        selected_players = random.sample(list(all_players), count)
        roll_position = roll["position"]
        theme_modifier = roll["theme_modifier"]

    # Persist the Roll record
    roll_record = Roll(
        position=roll_position,
        theme_modifier=theme_modifier,
        category_type=category_type if use_category else None,
        category_value=category_value if use_category else None,
        mode="quickplay",
    )
    session.add(roll_record)
    await session.flush()

    for idx, player in enumerate(selected_players):
        rp = RollPlayer(
            roll_id=roll_record.id,
            player_id=player.id,
            display_order=idx,
        )
        session.add(rp)

    await session.commit()
    await session.refresh(roll_record)

    return {
        "id": roll_record.id,
        "position": roll_record.position,
        "theme_modifier": roll_record.theme_modifier,
        "category_type": roll_record.category_type,
        "category_value": roll_record.category_value,
        "mode": "quickplay",
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
                "careerStats": p.career_stats,
                "peakStats": p.peak_stats,
                "playoffStats": p.playoff_stats,
                "allNbaSelections": p.all_nba_selections,
                "mvpVoteShares": p.mvp_vote_shares,
                "championships": p.championships,
                "allStarSelections": p.all_star_selections,
                "hofRank": p.hof_rank,
                "bbrefId": p.bbref_id,
                "team": p.team,
            }
            for p in selected_players
        ],
    }


@router.get("/rolls/{roll_id}")
async def get_roll(
    roll_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a Roll by ID with its players."""
    roll_result = await session.execute(
        select(Roll).where(Roll.id == roll_id)
    )
    roll_record = roll_result.scalar_one_or_none()

    if roll_record is None:
        raise HTTPException(status_code=404, detail="Roll not found")

    # Load players
    rp_result = await session.execute(
        select(Player)
        .join(RollPlayer, RollPlayer.player_id == Player.id)
        .where(RollPlayer.roll_id == roll_id)
        .order_by(RollPlayer.display_order)
    )
    players = list(rp_result.scalars().all())

    return {
        "id": roll_record.id,
        "position": roll_record.position,
        "theme_modifier": roll_record.theme_modifier,
        "mode": roll_record.mode,
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
                "career_stats": p.career_stats,
                "peak_stats": p.peak_stats,
                "playoff_stats": p.playoff_stats,
                "all_nba_selections": p.all_nba_selections,
                "mvp_vote_shares": p.mvp_vote_shares,
                "championships": p.championships,
                "all_star_selections": p.all_star_selections,
                "hof_rank": p.hof_rank,
                "bbref_id": p.bbref_id,
            }
            for p in players
        ],
    }


@router.get("/hoopiq", response_model=RollHoopIQResponse)
async def get_hoopiq(
    authorization: str | None = Header(default=None),
    category_type: str | None = None,
    category_value: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Generate a HoopIQ Roll with anonymized player data.

    Returns players with stats only (no names, photos, or team info).
    Authentication is optional.

    When category_type and category_value are provided, players are
    selected from the filtered category pool instead of the default
    position-based selection.
    """
    use_category = category_type is not None and category_value is not None

    if use_category:
        # Validate category_type
        if category_type not in CATEGORY_FILTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category_type '{category_type}'. Must be one of: {list(CATEGORY_FILTERS.keys())}",
            )

        # Query all players and use category-based selection
        result = await session.execute(select(Player))
        all_players = result.scalars().all()

        # Convert ORM objects to dicts for the category selection function
        player_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "position": p.position,
                "era": p.era,
                "team": p.team,
                "conference": p.conference,
                "career_stats": p.career_stats,
                "peak_stats": p.peak_stats,
                "playoff_stats": p.playoff_stats,
                "all_nba_selections": p.all_nba_selections,
                "mvp_vote_shares": p.mvp_vote_shares,
                "championships": p.championships,
                "all_star_selections": p.all_star_selections,
                "hof_rank": p.hof_rank,
                "bbref_id": p.bbref_id,
            }
            for p in all_players
        ]

        try:
            selected_dicts = select_players_by_category(
                category_type, category_value, player_dicts, count=5
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Map back to ORM player objects for consistent response building
        selected_ids = {d["id"] for d in selected_dicts}
        selected_players = [p for p in all_players if p.id in selected_ids]

        # Generate a random theme modifier to combine with the category
        theme_modifier = random.choice(THEME_MODIFIERS)

        # Use the category_type as the position field for compatibility
        if category_type == "position":
            roll_position = category_value
        else:
            roll_position = "Mixed"

    else:
        # Existing position-based behavior
        roll_data = generate_roll()

        position = roll_data["position"]
        valid_positions = POSITION_MAPPING.get(position)
        if valid_positions is None:
            raise HTTPException(status_code=500, detail=f"Unknown position: {position}")

        result = await session.execute(
            select(Player).where(Player.position.in_(valid_positions))
        )
        all_players = result.scalars().all()

        # Select 5 random players
        count = 5
        if len(all_players) < count:
            raise HTTPException(
                status_code=500,
                detail=f"Insufficient players for position '{position}': need {count}, found {len(all_players)}",
            )

        selected_players = random.sample(list(all_players), count)
        roll_position = roll_data["position"]
        theme_modifier = roll_data["theme_modifier"]

    # Persist Roll record
    roll_record = Roll(
        position=roll_position,
        theme_modifier=theme_modifier,
        category_type=category_type if use_category else None,
        category_value=category_value if use_category else None,
        mode="hoopiq",
    )
    session.add(roll_record)
    await session.flush()  # Get the roll ID

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

    await session.commit()

    # Build response with stats only (no names, photos, or team info)
    players_response = []
    for player in selected_players:
        player_resp = PlayerHoopIQResponse(
            id=player.id,
            career_stats=PlayerStats(**(player.career_stats or {})),
            peak_stats=PlayerStats(**(player.peak_stats or {})),
            playoff_stats=PlayerStats(**(player.playoff_stats or {})) if player.playoff_stats else None,
            all_nba_selections=player.all_nba_selections,
            all_star_selections=player.all_star_selections,
            championships=player.championships,
            mvp_vote_shares=player.mvp_vote_shares,
        )
        players_response.append(player_resp)

    return RollHoopIQResponse(
        id=roll_record.id,
        position=roll_position,
        theme_modifier=theme_modifier,
        mode="hoopiq",
        players=players_response,
    )
