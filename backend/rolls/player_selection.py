"""Player selection for a Roll.

Filters the player pool by position mapping and randomly selects
5–7 players for the ranking challenge.
"""

import random
from typing import Any


# Position mapping: maps a Roll position to the set of valid player positions
POSITION_MAPPING: dict[str, list[str]] = {
    "PG": ["PG"],
    "SG": ["SG"],
    "SF": ["SF"],
    "PF": ["PF"],
    "C": ["C"],
    "Wings": ["SG", "SF"],
    "Big Men": ["PF", "C"],
}


def select_players(
    roll: dict[str, str],
    pool: list[dict[str, Any]],
    count: int | None = None,
) -> list[dict[str, Any]]:
    """Select players from the pool matching the Roll's position.

    Filters the player pool to only those whose position matches the
    Roll's position mapping, then randomly selects `count` players.

    Args:
        roll: A Roll dictionary with at least a "position" key.
        pool: List of player dictionaries. Each must have a "position" field.
        count: Number of players to select (5–7). If None, a random value
            between 5 and 7 is chosen. Values outside 5–7 are clamped.

    Returns:
        A list of selected player dictionaries.

    Raises:
        ValueError: If the Roll's position is not recognized.
        ValueError: If the filtered pool has fewer players than requested.
    """
    position = roll["position"]

    if position not in POSITION_MAPPING:
        raise ValueError(
            f"Unknown position '{position}'. Must be one of: {list(POSITION_MAPPING.keys())}"
        )

    valid_positions = POSITION_MAPPING[position]

    # Filter players whose position matches the roll
    eligible = [p for p in pool if p.get("position") in valid_positions]

    # Determine count (5–7)
    if count is None:
        count = random.randint(5, 7)
    else:
        count = max(5, min(7, count))

    if len(eligible) < count:
        raise ValueError(
            f"Insufficient players for position '{position}': "
            f"need {count}, found {len(eligible)}"
        )

    return random.sample(eligible, count)
