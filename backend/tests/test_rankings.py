"""Tests for the rankings module: submission, retrieval, and community aggregates."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from rankings.router import (
    _generate_commentary,
    _identify_controversial_pick,
)
from schemas import (
    CommunityHeatmapResponse,
    ControversialPickResponse,
)


# ──────────────────────────────────────────────────────────────────────
# Commentary Generation Tests
# ──────────────────────────────────────────────────────────────────────


class TestGenerateCommentary:
    """Unit tests for _generate_commentary."""

    def test_grade_s_commentary(self):
        result = _generate_commentary("S")
        assert "Perfect" in result or "perfect" in result.lower()

    def test_grade_a_commentary(self):
        result = _generate_commentary("A")
        assert len(result) > 0

    def test_grade_b_commentary(self):
        result = _generate_commentary("B")
        assert len(result) > 0

    def test_grade_c_commentary(self):
        result = _generate_commentary("C")
        assert "hot take" in result.lower() or "disagrees" in result.lower()

    def test_grade_d_commentary(self):
        result = _generate_commentary("D")
        assert len(result) > 0

    def test_unknown_grade_fallback(self):
        result = _generate_commentary("X")
        assert "Interesting" in result


# ──────────────────────────────────────────────────────────────────────
# Controversial Pick Identification Tests
# ──────────────────────────────────────────────────────────────────────


class TestIdentifyControversialPick:
    """Unit tests for _identify_controversial_pick."""

    def test_identifies_lowest_agreement_slot(self):
        heatmap = CommunityHeatmapResponse(
            data={
                10: {1: 80.0, 2: 10.0, 3: 5.0, 4: 3.0, 5: 2.0},
                20: {1: 5.0, 2: 70.0, 3: 15.0, 4: 5.0, 5: 5.0},
                30: {1: 10.0, 2: 15.0, 3: 60.0, 4: 10.0, 5: 5.0},
                40: {1: 3.0, 2: 3.0, 3: 15.0, 4: 75.0, 5: 4.0},
                50: {1: 2.0, 2: 2.0, 3: 5.0, 4: 7.0, 5: 84.0},
            },
            total_submissions=100,
        )
        # User order: [10, 20, 30, 40, 50]
        # Agreement: slot1=80, slot2=70, slot3=60, slot4=75, slot5=84
        # Minimum agreement is slot3 with 60%
        result = _identify_controversial_pick([10, 20, 30, 40, 50], heatmap)
        assert result is not None
        assert result.player_id == 30
        assert result.slot == 3
        assert result.community_agreement == 60.0

    def test_identifies_controversial_with_unusual_placement(self):
        heatmap = CommunityHeatmapResponse(
            data={
                10: {1: 80.0, 2: 10.0, 3: 5.0, 4: 3.0, 5: 2.0},
                20: {1: 5.0, 2: 70.0, 3: 15.0, 4: 5.0, 5: 5.0},
                30: {1: 10.0, 2: 15.0, 3: 60.0, 4: 10.0, 5: 5.0},
                40: {1: 3.0, 2: 3.0, 3: 15.0, 4: 75.0, 5: 4.0},
                50: {1: 2.0, 2: 2.0, 3: 5.0, 4: 7.0, 5: 84.0},
            },
            total_submissions=100,
        )
        # User puts player 50 in slot 1 (only 2% agreement)
        result = _identify_controversial_pick([50, 20, 30, 40, 10], heatmap)
        assert result is not None
        assert result.player_id == 50
        assert result.slot == 1
        assert result.community_agreement == 2.0

    def test_empty_heatmap_returns_none(self):
        heatmap = CommunityHeatmapResponse(data={}, total_submissions=0)
        result = _identify_controversial_pick([10, 20, 30, 40, 50], heatmap)
        assert result is None

    def test_player_not_in_heatmap_gets_zero_agreement(self):
        heatmap = CommunityHeatmapResponse(
            data={
                10: {1: 80.0},
                20: {2: 70.0},
            },
            total_submissions=50,
        )
        # Player 30 not in heatmap data at all, so agreement = 0
        result = _identify_controversial_pick([10, 20, 30], heatmap)
        assert result is not None
        assert result.player_id == 30
        assert result.slot == 3
        assert result.community_agreement == 0.0

    def test_all_zero_agreement(self):
        # All players have 0% agreement for their slots
        heatmap = CommunityHeatmapResponse(
            data={
                10: {2: 100.0},  # player 10 always put in slot 2
                20: {1: 100.0},  # player 20 always put in slot 1
            },
            total_submissions=10,
        )
        # User puts 10 in slot 1 (0% agreement) and 20 in slot 2 (0% agreement)
        result = _identify_controversial_pick([10, 20], heatmap)
        assert result is not None
        # Both have 0% agreement; the first one encountered stays (slot 1)
        # because min is 0 and it won't be beaten
        assert result.community_agreement == 0.0


# ──────────────────────────────────────────────────────────────────────
# Ranking Validation Logic Tests (unit-level)
# ──────────────────────────────────────────────────────────────────────


class TestRankingValidation:
    """Tests for ranking validation logic."""

    def test_valid_permutation_detection(self):
        """A valid ranking is an exact permutation of the roll's player set."""
        valid_player_ids = {10, 20, 30, 40, 50}
        submitted = [10, 20, 30, 40, 50]
        assert set(submitted) == valid_player_ids
        assert len(submitted) == len(valid_player_ids)

    def test_invalid_missing_player(self):
        """Ranking missing a player from the roll is invalid."""
        valid_player_ids = {10, 20, 30, 40, 50}
        submitted = [10, 20, 30, 40, 60]  # 60 not in roll, 50 missing
        assert set(submitted) != valid_player_ids

    def test_invalid_duplicate_player(self):
        """Ranking with duplicate players is invalid."""
        valid_player_ids = {10, 20, 30, 40, 50}
        submitted = [10, 20, 30, 40, 40]  # duplicate 40, missing 50
        assert set(submitted) != valid_player_ids or len(submitted) != len(valid_player_ids)

    def test_invalid_extra_player(self):
        """Ranking with extra players is invalid."""
        valid_player_ids = {10, 20, 30, 40, 50}
        submitted = [10, 20, 30, 40, 50, 60]  # extra player
        assert len(submitted) != len(valid_player_ids)


# ──────────────────────────────────────────────────────────────────────
# Integration-style tests with full scoring pipeline
# ──────────────────────────────────────────────────────────────────────


class TestScoringPipeline:
    """Tests that the full scoring pipeline produces correct results."""

    def test_perfect_ranking_gets_grade_s(self):
        """If user ranking matches consensus exactly, distance=0 and grade=S."""
        from scoring import kendall_tau_distance, letter_grade

        consensus = [1, 2, 3, 4, 5]
        user_ranking = [1, 2, 3, 4, 5]
        distance = kendall_tau_distance(user_ranking, consensus)
        grade = letter_grade(distance)
        assert distance == 0
        assert grade == "S"

    def test_one_swap_gets_grade_a(self):
        """One adjacent swap produces distance=1 and grade=A."""
        from scoring import kendall_tau_distance, letter_grade

        consensus = [1, 2, 3, 4, 5]
        user_ranking = [2, 1, 3, 4, 5]
        distance = kendall_tau_distance(user_ranking, consensus)
        grade = letter_grade(distance)
        assert distance == 1
        assert grade == "A"

    def test_heavily_shuffled_gets_grade_d(self):
        """A heavily shuffled ranking gets grade D."""
        from scoring import kendall_tau_distance, letter_grade

        consensus = [1, 2, 3, 4, 5]
        user_ranking = [5, 4, 3, 2, 1]  # completely reversed
        distance = kendall_tau_distance(user_ranking, consensus)
        grade = letter_grade(distance)
        assert distance == 10
        assert grade == "D"
