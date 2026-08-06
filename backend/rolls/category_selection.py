"""Category-based player selection for Rolls.

Filters the player pool by category (position, team, decade, conference)
and randomly selects exactly 5 players for the ranking challenge.
"""

import random
from typing import Any, Callable

from .player_selection import POSITION_MAPPING


# Type alias for a filter function: takes a player list and a category value,
# returns the filtered subset.
FilterFn = Callable[[list[dict[str, Any]], str], list[dict[str, Any]]]


def _filter_by_position(players: list[dict[str, Any]], value: str) -> list[dict[str, Any]]:
    """Filter players by position, supporting composite values like Wings and Big Men."""
    valid_positions = POSITION_MAPPING.get(value)
    if valid_positions is None:
        raise ValueError(
            f"Unknown position value '{value}'. "
            f"Must be one of: {list(POSITION_MAPPING.keys())}"
        )
    return [p for p in players if p.get("position") in valid_positions]


def _filter_by_team(players: list[dict[str, Any]], value: str) -> list[dict[str, Any]]:
    """Filter players by primary team association."""
    return [p for p in players if p.get("team") == value]


def _filter_by_decade(players: list[dict[str, Any]], value: str) -> list[dict[str, Any]]:
    """Filter players by era/decade."""
    return [p for p in players if p.get("era") == value]


def _filter_by_conference(players: list[dict[str, Any]], value: str) -> list[dict[str, Any]]:
    """Filter players by conference."""
    return [p for p in players if p.get("conference") == value]


def _filter_all(players: list[dict[str, Any]], value: str) -> list[dict[str, Any]]:
    """No filter — return all players."""
    return players


CATEGORY_FILTERS: dict[str, FilterFn] = {
    "all": _filter_all,
    "position": _filter_by_position,
    "team": _filter_by_team,
    "decade": _filter_by_decade,
    "conference": _filter_by_conference,
}


def select_players_by_category(
    category_type: str,
    category_value: str,
    pool: list[dict[str, Any]],
    count: int = 5,
) -> list[dict[str, Any]]:
    """Filter the player pool by category, then randomly select `count` players.

    Args:
        category_type: One of "position", "team", "decade", "conference".
        category_value: The specific value within the category type
            (e.g., "PG", "Lakers", "1990s", "Eastern").
        pool: List of player dictionaries. Each must have the fields
            relevant to the category_type being filtered.
        count: Number of players to select. Defaults to 5.

    Returns:
        A list of exactly `count` randomly selected player dictionaries
        matching the category filter.

    Raises:
        ValueError: If category_type is not recognized.
        ValueError: If fewer than `count` players match the category filter.
    """
    filter_fn = CATEGORY_FILTERS.get(category_type)
    if filter_fn is None:
        raise ValueError(
            f"Unknown category_type '{category_type}'. "
            f"Must be one of: {list(CATEGORY_FILTERS.keys())}"
        )

    eligible = filter_fn(pool, category_value)

    if len(eligible) < count:
        raise ValueError(
            f"Insufficient players for {category_type}='{category_value}': "
            f"need {count}, found {len(eligible)}"
        )

    return random.sample(eligible, count)
