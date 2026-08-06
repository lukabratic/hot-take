"""Available Categories endpoint.

Returns all category types with their values, player counts, and disabled
status. Results are cached in Redis for 1 hour to avoid repeated DB queries.
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from config import settings
from database import get_session
from models import Player
from .player_selection import POSITION_MAPPING

router = APIRouter(prefix="/api/categories", tags=["categories"])

# Cache TTL: 1 hour in seconds
CACHE_TTL_SECONDS = 3600
CACHE_KEY = "category_counts"

# NBA teams grouped by conference
EASTERN_TEAMS = [
    "76ers", "Bucks", "Bulls", "Cavaliers", "Celtics",
    "Hawks", "Heat", "Hornets", "Knicks", "Magic",
    "Nets", "Pacers", "Pistons", "Raptors", "Wizards",
]

WESTERN_TEAMS = [
    "Clippers", "Grizzlies", "Jazz", "Kings", "Lakers",
    "Mavericks", "Nuggets", "Pelicans", "Rockets", "Spurs",
    "Suns", "Thunder", "Timberwolves", "Trail Blazers", "Warriors",
]

ALL_TEAMS = sorted(EASTERN_TEAMS + WESTERN_TEAMS)

# Category value definitions with labels
CATEGORY_DEFINITIONS: dict[str, list[dict[str, str]]] = {
    "all": [
        {"value": "All Players", "label": "All Players"},
    ],
    "position": [
        {"value": "PG", "label": "Point Guard"},
        {"value": "SG", "label": "Shooting Guard"},
        {"value": "SF", "label": "Small Forward"},
        {"value": "PF", "label": "Power Forward"},
        {"value": "C", "label": "Center"},
        {"value": "Wings", "label": "Wings"},
        {"value": "Big Men", "label": "Big Men"},
    ],
    "team": [{"value": t, "label": t} for t in ALL_TEAMS],
    "decade": [
        {"value": "1960s", "label": "1960s"},
        {"value": "1970s", "label": "1970s"},
        {"value": "1980s", "label": "1980s"},
        {"value": "1990s", "label": "1990s"},
        {"value": "2000s", "label": "2000s"},
        {"value": "2010s", "label": "2010s"},
        {"value": "2020s", "label": "2020s"},
    ],
    "conference": [
        {"value": "Eastern", "label": "Eastern Conference"},
        {"value": "Western", "label": "Western Conference"},
    ],
}

MIN_PLAYERS = 5


async def get_redis() -> redis.Redis:
    """FastAPI dependency that yields an async Redis client."""
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def _get_position_counts(session: AsyncSession) -> dict[str, int]:
    """Query player counts for each position category value.

    Composite positions (Wings, Big Men) are computed from individual counts.
    """
    result = await session.execute(
        select(Player.position, func.count(Player.id)).group_by(Player.position)
    )
    raw_counts: dict[str, int] = {row[0]: row[1] for row in result.all()}

    position_counts: dict[str, int] = {}
    for value, mapped_positions in POSITION_MAPPING.items():
        position_counts[value] = sum(
            raw_counts.get(pos, 0) for pos in mapped_positions
        )
    return position_counts


async def _get_team_counts(session: AsyncSession) -> dict[str, int]:
    """Query player counts per team."""
    result = await session.execute(
        select(Player.team, func.count(Player.id))
        .where(Player.team.isnot(None))
        .group_by(Player.team)
    )
    return {row[0]: row[1] for row in result.all()}


async def _get_decade_counts(session: AsyncSession) -> dict[str, int]:
    """Query player counts per era/decade."""
    result = await session.execute(
        select(Player.era, func.count(Player.id))
        .where(Player.era.isnot(None))
        .group_by(Player.era)
    )
    return {row[0]: row[1] for row in result.all()}


async def _get_conference_counts(session: AsyncSession) -> dict[str, int]:
    """Query player counts per conference."""
    result = await session.execute(
        select(Player.conference, func.count(Player.id))
        .where(Player.conference.isnot(None))
        .group_by(Player.conference)
    )
    return {row[0]: row[1] for row in result.all()}


async def _build_categories_response(session: AsyncSession) -> dict:
    """Build the full categories response by querying player counts."""
    position_counts = await _get_position_counts(session)
    team_counts = await _get_team_counts(session)
    decade_counts = await _get_decade_counts(session)
    conference_counts = await _get_conference_counts(session)

    # Total player count for "All" category
    total_result = await session.execute(select(func.count(Player.id)))
    total_players = total_result.scalar() or 0
    all_counts = {"All Players": total_players}

    count_maps = {
        "all": all_counts,
        "position": position_counts,
        "team": team_counts,
        "decade": decade_counts,
        "conference": conference_counts,
    }

    response: dict[str, list[dict]] = {}
    for category_type, definitions in CATEGORY_DEFINITIONS.items():
        counts = count_maps[category_type]
        response[category_type] = [
            {
                "value": defn["value"],
                "label": defn["label"],
                "playerCount": counts.get(defn["value"], 0),
                "disabled": counts.get(defn["value"], 0) < MIN_PLAYERS,
            }
            for defn in definitions
        ]

    return response


@router.get("/available")
async def get_available_categories(
    redis_client: redis.Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    """Return all category types with their values and player counts.

    Results are cached in Redis for 1 hour. Categories with fewer than
    5 players are marked as disabled.
    """
    # Try cache first
    cached = await redis_client.get(CACHE_KEY)
    if cached is not None:
        return json.loads(cached)

    # Build response from database
    response = await _build_categories_response(session)

    # Cache in Redis with 1-hour TTL
    await redis_client.set(CACHE_KEY, json.dumps(response), ex=CACHE_TTL_SECONDS)

    return response
