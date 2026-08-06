"""Unit tests for the Roll System."""

import pytest
from rolls.generator import generate_roll, POSITIONS, THEME_MODIFIERS
from rolls.player_selection import select_players, POSITION_MAPPING


class TestGenerateRoll:
    """Tests for generate_roll function."""

    def test_returns_position_and_theme(self):
        roll = generate_roll()
        assert "position" in roll
        assert "theme_modifier" in roll

    def test_random_position_is_valid(self):
        roll = generate_roll()
        assert roll["position"] in POSITIONS

    def test_random_theme_is_valid(self):
        roll = generate_roll()
        assert roll["theme_modifier"] in THEME_MODIFIERS

    def test_specific_position(self):
        roll = generate_roll(position="PG")
        assert roll["position"] == "PG"

    def test_specific_theme_modifier(self):
        roll = generate_roll(theme_modifier="Peak Season Only")
        assert roll["theme_modifier"] == "Peak Season Only"

    def test_both_specified(self):
        roll = generate_roll(position="Wings", theme_modifier="Defensive Impact")
        assert roll["position"] == "Wings"
        assert roll["theme_modifier"] == "Defensive Impact"

    def test_invalid_position_raises(self):
        with pytest.raises(ValueError, match="Invalid position"):
            generate_roll(position="Center")

    def test_invalid_theme_raises(self):
        with pytest.raises(ValueError, match="Invalid theme modifier"):
            generate_roll(theme_modifier="Best Dunker")


class TestSelectPlayers:
    """Tests for select_players function."""

    @pytest.fixture
    def player_pool(self):
        """A minimal player pool covering all positions."""
        players = []
        for i, pos in enumerate(["PG"] * 8 + ["SG"] * 8 + ["SF"] * 8 + ["PF"] * 8 + ["C"] * 8):
            players.append({
                "id": i + 1,
                "name": f"Player {i + 1}",
                "position": pos,
            })
        return players

    def test_selects_correct_count(self, player_pool):
        roll = {"position": "PG"}
        result = select_players(roll, player_pool, count=5)
        assert len(result) == 5

    def test_all_match_position(self, player_pool):
        roll = {"position": "SG"}
        result = select_players(roll, player_pool, count=6)
        assert all(p["position"] == "SG" for p in result)

    def test_wings_selects_sg_or_sf(self, player_pool):
        roll = {"position": "Wings"}
        result = select_players(roll, player_pool, count=7)
        assert all(p["position"] in ("SG", "SF") for p in result)

    def test_big_men_selects_pf_or_c(self, player_pool):
        roll = {"position": "Big Men"}
        result = select_players(roll, player_pool, count=5)
        assert all(p["position"] in ("PF", "C") for p in result)

    def test_random_count_in_range(self, player_pool):
        roll = {"position": "PG"}
        result = select_players(roll, player_pool)
        assert 5 <= len(result) <= 7

    def test_insufficient_players_raises(self):
        small_pool = [{"id": 1, "name": "Player 1", "position": "PG"}]
        roll = {"position": "PG"}
        with pytest.raises(ValueError, match="Insufficient players"):
            select_players(roll, small_pool, count=5)

    def test_invalid_position_raises(self, player_pool):
        roll = {"position": "Invalid"}
        with pytest.raises(ValueError, match="Unknown position"):
            select_players(roll, player_pool, count=5)

    def test_count_clamped_to_minimum(self, player_pool):
        roll = {"position": "PG"}
        result = select_players(roll, player_pool, count=2)
        assert len(result) == 5  # clamped to minimum of 5

    def test_count_clamped_to_maximum(self, player_pool):
        roll = {"position": "PG"}
        result = select_players(roll, player_pool, count=10)
        assert len(result) == 7  # clamped to maximum of 7
