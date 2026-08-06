"""Unit tests for streak tracking logic.

Validates the streak state machine:
- Consecutive days increment the streak
- Gaps reset the streak
- Same-day completions are idempotent
- Longest streak is tracked correctly

Requirements: 11.1, 11.2, 11.4
"""

from datetime import date, timedelta

import pytest

from models import User
from streak.logic import update_streak


def _make_user(
    current_streak: int = 0,
    longest_streak: int = 0,
    last_daily_completed: date | None = None,
) -> User:
    """Create a minimal User instance for testing streak logic."""
    user = User(
        clerk_id="test_clerk_id",
        username="test_user",
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_daily_completed=last_daily_completed,
    )
    return user


class TestUpdateStreak:
    """Tests for the update_streak function."""

    def test_first_ever_completion_sets_streak_to_one(self):
        user = _make_user()
        update_streak(user, date(2025, 6, 15))

        assert user.current_streak == 1
        assert user.longest_streak == 1
        assert user.last_daily_completed == date(2025, 6, 15)

    def test_consecutive_day_increments_streak(self):
        user = _make_user(
            current_streak=3,
            longest_streak=5,
            last_daily_completed=date(2025, 6, 14),
        )
        update_streak(user, date(2025, 6, 15))

        assert user.current_streak == 4
        assert user.longest_streak == 5  # Unchanged since 4 < 5
        assert user.last_daily_completed == date(2025, 6, 15)

    def test_consecutive_day_updates_longest_streak(self):
        user = _make_user(
            current_streak=5,
            longest_streak=5,
            last_daily_completed=date(2025, 6, 14),
        )
        update_streak(user, date(2025, 6, 15))

        assert user.current_streak == 6
        assert user.longest_streak == 6
        assert user.last_daily_completed == date(2025, 6, 15)

    def test_gap_of_two_days_resets_streak(self):
        user = _make_user(
            current_streak=10,
            longest_streak=10,
            last_daily_completed=date(2025, 6, 13),
        )
        update_streak(user, date(2025, 6, 15))

        assert user.current_streak == 1
        assert user.longest_streak == 10  # Preserved
        assert user.last_daily_completed == date(2025, 6, 15)

    def test_same_day_completion_is_idempotent(self):
        user = _make_user(
            current_streak=3,
            longest_streak=5,
            last_daily_completed=date(2025, 6, 15),
        )
        update_streak(user, date(2025, 6, 15))

        # Nothing should change
        assert user.current_streak == 3
        assert user.longest_streak == 5
        assert user.last_daily_completed == date(2025, 6, 15)

    def test_long_gap_resets_streak(self):
        user = _make_user(
            current_streak=50,
            longest_streak=50,
            last_daily_completed=date(2025, 1, 1),
        )
        update_streak(user, date(2025, 6, 15))

        assert user.current_streak == 1
        assert user.longest_streak == 50

    def test_streak_builds_over_multiple_consecutive_days(self):
        user = _make_user()
        start = date(2025, 6, 1)

        for i in range(7):
            update_streak(user, start + timedelta(days=i))

        assert user.current_streak == 7
        assert user.longest_streak == 7
        assert user.last_daily_completed == date(2025, 6, 7)

    def test_streak_resets_then_rebuilds(self):
        user = _make_user(
            current_streak=3,
            longest_streak=3,
            last_daily_completed=date(2025, 6, 3),
        )
        # Gap — skip June 4
        update_streak(user, date(2025, 6, 5))
        assert user.current_streak == 1

        # Build again
        update_streak(user, date(2025, 6, 6))
        assert user.current_streak == 2

        update_streak(user, date(2025, 6, 7))
        assert user.current_streak == 3

        update_streak(user, date(2025, 6, 8))
        assert user.current_streak == 4
        assert user.longest_streak == 4  # New longest
