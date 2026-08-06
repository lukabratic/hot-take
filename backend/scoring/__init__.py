"""Scoring engine for Hot Take NBA Ranking Game.

Provides Kendall tau distance computation, letter grade assignment,
and consensus ranking generation.
"""

from .kendall_tau import kendall_tau_distance
from .grading import letter_grade
from .consensus import (
    compute_analytics_consensus,
    compute_reputation_consensus,
)

__all__ = [
    "kendall_tau_distance",
    "letter_grade",
    "compute_analytics_consensus",
    "compute_reputation_consensus",
]
