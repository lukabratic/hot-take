"""Streak update logic for daily challenge completions.

Implements the streak state machine:
- If last_daily_completed == yesterday: increment streak
- If last_daily_completed == today: no change (already completed)
- Otherwise: reset streak to 1 (new streak starts)

Requirements: 11.1, 11.2
"""

from datetime import date, timedelta

from models import User


def update_streak(user: User, completion_date: date) -> None:
    """Update a user's streak based on daily challenge completion.

    Mutates the user model in place. The caller is responsible
    for committing the session.

    Args:
        user: The user who completed the daily challenge.
        completion_date: The UTC date of the daily challenge completed.
    """
    if user.last_daily_completed == completion_date:
        # Already completed today — no streak change
        return

    yesterday = completion_date - timedelta(days=1)

    if user.last_daily_completed == yesterday:
        # Consecutive day: increment the streak
        user.current_streak += 1
    else:
        # Gap in completions (or first ever): start a new streak
        user.current_streak = 1

    # Update longest streak if needed
    if user.current_streak > user.longest_streak:
        user.longest_streak = user.current_streak

    # Record completion date
    user.last_daily_completed = completion_date
