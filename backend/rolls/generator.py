"""Roll generation logic.

Generates a Roll consisting of a Position and Theme Modifier combination
that defines the ranking challenge for a game session.
"""

import random
from typing import Literal

# Supported positions for Roll generation
POSITIONS: list[str] = ["PG", "SG", "SF", "PF", "C", "Wings", "Big Men"]

# Supported theme modifiers for Roll generation
THEME_MODIFIERS: list[str] = [
    "All-Time",
    "Peak Season Only",
    "Playoff Performance",
    "Defensive Impact",
    "Regular Season Only",
    "Championship Era Only",
]


def generate_roll(
    position: str | None = None,
    theme_modifier: str | None = None,
) -> dict[str, str]:
    """Generate a Roll with a position and theme modifier.

    If position or theme_modifier are not specified, they are randomly
    selected from the supported values.

    Args:
        position: A basketball position category. One of PG, SG, SF, PF, C,
            Wings, or Big Men. If None, one is chosen at random.
        theme_modifier: A theme constraint for the Roll. One of All-Time,
            Peak Season Only, Playoff Performance, Defensive Impact,
            Regular Season Only, or Championship Era Only. If None, one is
            chosen at random.

    Returns:
        A dictionary with "position" and "theme_modifier" keys.

    Raises:
        ValueError: If an invalid position or theme_modifier is provided.
    """
    if position is not None and position not in POSITIONS:
        raise ValueError(
            f"Invalid position '{position}'. Must be one of: {POSITIONS}"
        )

    if theme_modifier is not None and theme_modifier not in THEME_MODIFIERS:
        raise ValueError(
            f"Invalid theme modifier '{theme_modifier}'. Must be one of: {THEME_MODIFIERS}"
        )

    selected_position = position if position is not None else random.choice(POSITIONS)
    selected_theme = theme_modifier if theme_modifier is not None else random.choice(THEME_MODIFIERS)

    return {
        "position": selected_position,
        "theme_modifier": selected_theme,
    }
