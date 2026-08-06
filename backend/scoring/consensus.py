"""Consensus ranking generation.

Computes reference rankings for a set of players based on either
analytics-driven statistics or reputation-driven accolades. The
consensus ranking serves as the "correct answer" against which
user rankings are scored.
"""

from typing import Any

# Theme modifier constants
THEME_ALL_TIME = "All-Time"
THEME_PEAK_SEASON = "Peak Season Only"
THEME_PLAYOFF = "Playoff Performance"
THEME_DEFENSIVE = "Defensive Impact"
THEME_REGULAR_SEASON = "Regular Season Only"
THEME_CHAMPIONSHIP = "Championship Era Only"

# Analytics rubric weights
ANALYTICS_WEIGHTS = {
    "vorp": 0.30,
    "bpm": 0.25,
    "ws": 0.25,
    "per": 0.20,
}

# Defensive emphasis weights (used when theme is Defensive Impact)
DEFENSIVE_WEIGHTS = {
    "bpm": 0.20,
    "vorp": 0.15,
    "ws": 0.15,
    "per": 0.10,
    "blk": 0.20,
    "stl": 0.20,
}

# Reputation rubric weights
REPUTATION_WEIGHTS = {
    "all_nba_selections": 0.30,
    "mvp_vote_shares": 0.30,
    "hof_rank": 0.20,
    "all_star_selections": 0.20,
}


def _get_stats_for_theme(player: dict[str, Any], theme_modifier: str) -> dict[str, float]:
    """Select the appropriate stats dict based on theme modifier.

    Args:
        player: Player data dictionary with career_stats, peak_stats, playoff_stats.
        theme_modifier: The theme modifier string.

    Returns:
        The appropriate stats dictionary for scoring.
    """
    if theme_modifier == THEME_PEAK_SEASON:
        return player.get("peak_stats") or player.get("career_stats") or {}
    elif theme_modifier == THEME_PLAYOFF:
        return player.get("playoff_stats") or player.get("career_stats") or {}
    elif theme_modifier == THEME_CHAMPIONSHIP:
        # Use championship-era stats if available, fall back to career
        return player.get("championship_stats") or player.get("career_stats") or {}
    else:
        # All-Time, Regular Season Only, and default use career_stats
        return player.get("career_stats") or {}


def _compute_analytics_score(stats: dict[str, float], theme_modifier: str) -> float:
    """Compute a weighted composite analytics score from player stats.

    Args:
        stats: Dictionary of player statistics.
        theme_modifier: The theme modifier (affects weighting for Defensive Impact).

    Returns:
        Weighted composite score.
    """
    if theme_modifier == THEME_DEFENSIVE:
        weights = DEFENSIVE_WEIGHTS
    else:
        weights = ANALYTICS_WEIGHTS

    score = 0.0
    for stat_key, weight in weights.items():
        value = stats.get(stat_key, 0.0)
        if value is None:
            value = 0.0
        score += float(value) * weight

    return score


def _compute_reputation_score(player: dict[str, Any]) -> float:
    """Compute a weighted composite reputation score from player accolades.

    The HOF rank is inverted so that a lower rank number (more prestigious)
    produces a higher score.

    Args:
        player: Player data dictionary with accolade fields.

    Returns:
        Weighted composite reputation score.
    """
    all_nba = float(player.get("all_nba_selections", 0) or 0)
    mvp_shares = float(player.get("mvp_vote_shares", 0.0) or 0.0)
    hof_rank = player.get("hof_rank")
    all_star = float(player.get("all_star_selections", 0) or 0)

    # Invert HOF rank: lower rank = better. Use 0 for non-HOF players.
    # Scale: rank 1 -> high score, rank 100 -> low score
    if hof_rank is not None and hof_rank > 0:
        hof_score = max(0.0, 100.0 - float(hof_rank))
    else:
        hof_score = 0.0

    score = (
        all_nba * REPUTATION_WEIGHTS["all_nba_selections"]
        + mvp_shares * REPUTATION_WEIGHTS["mvp_vote_shares"]
        + hof_score * REPUTATION_WEIGHTS["hof_rank"]
        + all_star * REPUTATION_WEIGHTS["all_star_selections"]
    )

    return score


def compute_analytics_consensus(
    players: list[dict[str, Any]], theme_modifier: str
) -> list[int]:
    """Compute the analytics-based consensus ranking for a set of players.

    Sorts players by a weighted composite of era-adjusted VORP, BPM,
    Win Shares, and PER. The theme modifier determines which stat source
    (career, peak, playoff) is used.

    Args:
        players: List of player dictionaries. Each must have an "id" field
            and stats fields (career_stats, peak_stats, playoff_stats).
        theme_modifier: One of the ThemeModifier values determining which
            stats to use for the composite calculation.

    Returns:
        Ordered list of player IDs from best to worst (descending composite score).
    """
    scored_players = []
    for player in players:
        stats = _get_stats_for_theme(player, theme_modifier)
        score = _compute_analytics_score(stats, theme_modifier)
        scored_players.append((player["id"], score))

    # Sort by score descending; break ties by player ID for determinism
    scored_players.sort(key=lambda x: (-x[1], x[0]))

    return [player_id for player_id, _ in scored_players]


def compute_reputation_consensus(
    players: list[dict[str, Any]], theme_modifier: str
) -> list[int]:
    """Compute the reputation-based consensus ranking for a set of players.

    Sorts players by a weighted composite of All-NBA selections, MVP vote
    shares, Hall of Fame rank, and All-Star selections.

    Note: The theme_modifier parameter is accepted for API consistency but
    reputation scoring is based on career accolades which are not
    theme-dependent. Future versions may adjust weights by theme.

    Args:
        players: List of player dictionaries. Each must have an "id" field
            and accolade fields (all_nba_selections, mvp_vote_shares,
            hof_rank, all_star_selections).
        theme_modifier: Theme modifier string (accepted for interface
            consistency; does not affect reputation scoring).

    Returns:
        Ordered list of player IDs from best to worst (descending composite score).
    """
    scored_players = []
    for player in players:
        score = _compute_reputation_score(player)
        scored_players.append((player["id"], score))

    # Sort by score descending; break ties by player ID for determinism
    scored_players.sort(key=lambda x: (-x[1], x[0]))

    return [player_id for player_id, _ in scored_players]
