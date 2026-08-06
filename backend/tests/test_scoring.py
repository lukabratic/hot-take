"""Tests for the scoring engine: Kendall tau, grading, and consensus."""
import pytest
from scoring.kendall_tau import kendall_tau_distance
from scoring.grading import letter_grade
from scoring.consensus import (
    compute_analytics_consensus,
    compute_reputation_consensus,
    THEME_ALL_TIME,
    THEME_PEAK_SEASON,
    THEME_PLAYOFF,
    THEME_DEFENSIVE,
)


# ──────────────────────────────────────────────────────────────────────
# Kendall Tau Distance Tests
# ──────────────────────────────────────────────────────────────────────


class TestKendallTauDistance:
    """Unit tests for kendall_tau_distance."""

    def test_identical_rankings_return_zero(self):
        assert kendall_tau_distance([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == 0

    def test_single_adjacent_swap(self):
        # Swapping positions 1 and 2 produces exactly 1 inversion
        assert kendall_tau_distance([1, 2, 3, 4, 5], [2, 1, 3, 4, 5]) == 1

    def test_fully_reversed_ranking(self):
        # Reversed list of length 5: max distance = 5*4/2 = 10
        assert kendall_tau_distance([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == 10

    def test_symmetry(self):
        a = [1, 2, 3, 4, 5]
        b = [3, 1, 4, 5, 2]
        assert kendall_tau_distance(a, b) == kendall_tau_distance(b, a)

    def test_length_six(self):
        # Max for length 6: 6*5/2 = 15
        assert kendall_tau_distance([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]) == 15

    def test_length_seven(self):
        # Max for length 7: 7*6/2 = 21
        assert kendall_tau_distance(
            [1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1]
        ) == 21

    def test_single_element_returns_zero(self):
        assert kendall_tau_distance([42], [42]) == 0

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError):
            kendall_tau_distance([1, 2, 3], [1, 2])

    def test_different_elements_raises(self):
        with pytest.raises(ValueError):
            kendall_tau_distance([1, 2, 3], [4, 5, 6])

    def test_known_distance_three(self):
        # [1,2,3,4,5] vs [1,3,4,2,5]: inversions: (2,3),(2,4) -> 2 actually
        # Let's do a precise example: [1,2,3,4,5] vs [2,3,1,4,5]
        # Pairs inverted: (1,2), (1,3) -> distance = 2
        assert kendall_tau_distance([1, 2, 3, 4, 5], [2, 3, 1, 4, 5]) == 2

    def test_bounded_output(self):
        """Distance must be in [0, N*(N-1)/2]."""
        a = [10, 20, 30, 40, 50]
        b = [30, 10, 50, 20, 40]
        dist = kendall_tau_distance(a, b)
        n = len(a)
        assert 0 <= dist <= n * (n - 1) // 2


# ──────────────────────────────────────────────────────────────────────
# Letter Grade Tests
# ──────────────────────────────────────────────────────────────────────


class TestLetterGrade:
    """Unit tests for letter_grade."""

    def test_grade_s(self):
        assert letter_grade(0) == "S"

    def test_grade_a_boundary_low(self):
        assert letter_grade(1) == "A"

    def test_grade_a_boundary_high(self):
        assert letter_grade(2) == "A"

    def test_grade_b_boundary_low(self):
        assert letter_grade(3) == "B"

    def test_grade_b_boundary_high(self):
        assert letter_grade(4) == "B"

    def test_grade_c_boundary_low(self):
        assert letter_grade(5) == "C"

    def test_grade_c_boundary_high(self):
        assert letter_grade(6) == "C"

    def test_grade_d_boundary(self):
        assert letter_grade(7) == "D"

    def test_grade_d_large_distance(self):
        assert letter_grade(21) == "D"

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            letter_grade(-1)

    def test_all_valid_grades(self):
        """Every distance in [0, 21] should produce a valid grade."""
        valid_grades = {"S", "A", "B", "C", "D"}
        for d in range(22):
            assert letter_grade(d) in valid_grades


# ──────────────────────────────────────────────────────────────────────
# Analytics Consensus Tests
# ──────────────────────────────────────────────────────────────────────


class TestAnalyticsConsensus:
    """Unit tests for compute_analytics_consensus."""

    def _make_player(self, pid, vorp, bpm, ws, per, peak=None, playoff=None):
        """Helper to create a player dict."""
        career = {"vorp": vorp, "bpm": bpm, "ws": ws, "per": per}
        player = {
            "id": pid,
            "career_stats": career,
            "peak_stats": peak or career,
            "playoff_stats": playoff or career,
        }
        return player

    def test_sorts_by_descending_composite(self):
        players = [
            self._make_player(1, vorp=5.0, bpm=4.0, ws=8.0, per=22.0),
            self._make_player(2, vorp=8.0, bpm=6.0, ws=12.0, per=28.0),
            self._make_player(3, vorp=3.0, bpm=2.0, ws=5.0, per=18.0),
        ]
        result = compute_analytics_consensus(players, THEME_ALL_TIME)
        # Player 2 has highest stats, player 1 middle, player 3 lowest
        assert result == [2, 1, 3]

    def test_uses_peak_stats_for_peak_theme(self):
        players = [
            self._make_player(
                1, vorp=3.0, bpm=2.0, ws=5.0, per=18.0,
                peak={"vorp": 10.0, "bpm": 9.0, "ws": 15.0, "per": 30.0},
            ),
            self._make_player(
                2, vorp=8.0, bpm=6.0, ws=12.0, per=28.0,
                peak={"vorp": 6.0, "bpm": 5.0, "ws": 10.0, "per": 24.0},
            ),
        ]
        result = compute_analytics_consensus(players, THEME_PEAK_SEASON)
        # Player 1 has better peak stats
        assert result == [1, 2]

    def test_uses_playoff_stats_for_playoff_theme(self):
        players = [
            self._make_player(
                1, vorp=8.0, bpm=6.0, ws=12.0, per=28.0,
                playoff={"vorp": 2.0, "bpm": 1.0, "ws": 3.0, "per": 15.0},
            ),
            self._make_player(
                2, vorp=3.0, bpm=2.0, ws=5.0, per=18.0,
                playoff={"vorp": 9.0, "bpm": 7.0, "ws": 14.0, "per": 30.0},
            ),
        ]
        result = compute_analytics_consensus(players, THEME_PLAYOFF)
        # Player 2 has better playoff stats
        assert result == [2, 1]

    def test_defensive_theme_weights_defense(self):
        # Player with high defensive stats should rank higher with defensive theme
        # Defensive weights: vorp=0.15, bpm=0.20, ws=0.15, per=0.10, blk=0.20, stl=0.20
        # Player 1: similar traditional stats but elite defensive stats
        # Player 2: slightly better traditional stats but poor defensive stats
        players = [
            {
                "id": 1,
                "career_stats": {
                    "vorp": 4.0, "bpm": 3.0, "ws": 6.0, "per": 20.0,
                    "blk": 4.0, "stl": 3.0,
                },
                "peak_stats": {},
                "playoff_stats": {},
            },
            {
                "id": 2,
                "career_stats": {
                    "vorp": 5.0, "bpm": 4.0, "ws": 7.0, "per": 22.0,
                    "blk": 0.3, "stl": 0.3,
                },
                "peak_stats": {},
                "playoff_stats": {},
            },
        ]
        result = compute_analytics_consensus(players, THEME_DEFENSIVE)
        # Player 1 score: 4*0.15 + 3*0.20 + 6*0.15 + 20*0.10 + 4*0.20 + 3*0.20 = 0.6+0.6+0.9+2.0+0.8+0.6 = 5.5
        # Player 2 score: 5*0.15 + 4*0.20 + 7*0.15 + 22*0.10 + 0.3*0.20 + 0.3*0.20 = 0.75+0.8+1.05+2.2+0.06+0.06 = 4.92
        assert result[0] == 1

    def test_empty_players_returns_empty(self):
        assert compute_analytics_consensus([], THEME_ALL_TIME) == []

    def test_single_player(self):
        players = [self._make_player(99, vorp=5.0, bpm=4.0, ws=8.0, per=22.0)]
        assert compute_analytics_consensus(players, THEME_ALL_TIME) == [99]


# ──────────────────────────────────────────────────────────────────────
# Reputation Consensus Tests
# ──────────────────────────────────────────────────────────────────────


class TestReputationConsensus:
    """Unit tests for compute_reputation_consensus."""

    def _make_player(self, pid, all_nba, mvp_shares, hof_rank, all_star):
        return {
            "id": pid,
            "all_nba_selections": all_nba,
            "mvp_vote_shares": mvp_shares,
            "hof_rank": hof_rank,
            "all_star_selections": all_star,
        }

    def test_sorts_by_descending_reputation_score(self):
        players = [
            self._make_player(1, all_nba=15, mvp_shares=8.0, hof_rank=1, all_star=18),
            self._make_player(2, all_nba=5, mvp_shares=1.0, hof_rank=50, all_star=8),
            self._make_player(3, all_nba=10, mvp_shares=4.0, hof_rank=10, all_star=13),
        ]
        result = compute_reputation_consensus(players, THEME_ALL_TIME)
        # Player 1 has best accolades by far
        assert result[0] == 1
        # Player 3 should beat player 2
        assert result[1] == 3
        assert result[2] == 2

    def test_non_hof_player_gets_zero_hof_score(self):
        players = [
            self._make_player(1, all_nba=5, mvp_shares=2.0, hof_rank=None, all_star=5),
            self._make_player(2, all_nba=5, mvp_shares=2.0, hof_rank=10, all_star=5),
        ]
        result = compute_reputation_consensus(players, THEME_ALL_TIME)
        # Player 2 has HOF rank, should score higher
        assert result[0] == 2

    def test_empty_players_returns_empty(self):
        assert compute_reputation_consensus([], THEME_ALL_TIME) == []

    def test_theme_modifier_does_not_affect_reputation(self):
        players = [
            self._make_player(1, all_nba=10, mvp_shares=5.0, hof_rank=5, all_star=12),
            self._make_player(2, all_nba=3, mvp_shares=0.5, hof_rank=80, all_star=4),
        ]
        result_all_time = compute_reputation_consensus(players, THEME_ALL_TIME)
        result_peak = compute_reputation_consensus(players, THEME_PEAK_SEASON)
        result_playoff = compute_reputation_consensus(players, THEME_PLAYOFF)
        assert result_all_time == result_peak == result_playoff
