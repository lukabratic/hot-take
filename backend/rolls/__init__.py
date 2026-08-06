"""Roll system for Hot Take NBA Ranking Game.

Provides Roll generation, player selection, daily challenge management,
and Quick Play deduplication.
"""

from .generator import generate_roll
from .player_selection import select_players

__all__ = [
    "generate_roll",
    "select_players",
]
