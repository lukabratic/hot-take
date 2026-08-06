"""Profile API endpoint returning user stats and ranking history."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from database import get_session
from models import Ranking, Roll, User
from schemas import (
    CategoryBestEntry,
    CategoryBestsResponse,
    ProfileRankingHistoryEntry,
    ProfileStatsResponse,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Grade to numeric value mapping for average computation
GRADE_VALUES = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
GRADE_ORDER = ["S", "A", "B", "C", "D"]


@router.get("", response_model=ProfileStatsResponse)
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileStatsResponse:
    """Get the authenticated user's profile with aggregated stats.

    Returns total games played, average grade, best grade, streak info,
    grade distribution, and recent ranking history (last 20).
    """
    # Fetch all rankings for this user, joined with Roll for context
    result = await session.execute(
        select(Ranking, Roll)
        .join(Roll, Ranking.roll_id == Roll.id)
        .where(Ranking.user_id == current_user.id)
        .order_by(Ranking.created_at.desc())
    )
    rows = result.all()

    total_games = len(rows)

    # Compute stats from rankings
    grade_distribution: dict[str, int] = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    grade_sum = 0.0
    best_grade = "D"

    for ranking, _roll in rows:
        grade = ranking.letter_grade
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        grade_sum += GRADE_VALUES.get(grade, 1)

        # Track best grade (lowest index in GRADE_ORDER is best)
        if GRADE_ORDER.index(grade) < GRADE_ORDER.index(best_grade):
            best_grade = grade

    average_grade = grade_sum / total_games if total_games > 0 else 0.0

    # Build recent history (last 20)
    recent_history: list[ProfileRankingHistoryEntry] = []
    for ranking, roll in rows[:20]:
        recent_history.append(
            ProfileRankingHistoryEntry(
                id=ranking.id,
                roll_position=roll.position,
                roll_theme_modifier=roll.theme_modifier,
                letter_grade=ranking.letter_grade,
                mode=ranking.mode,
                rubric=ranking.rubric,
                kendall_tau_distance=ranking.kendall_tau_distance,
                created_at=ranking.created_at,
            )
        )

    return ProfileStatsResponse(
        id=current_user.id,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        total_games=total_games,
        average_grade=round(average_grade, 2),
        best_grade=best_grade if total_games > 0 else "N/A",
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        grade_distribution=grade_distribution,
        recent_history=recent_history,
    )


# Grade to score mapping (same as leaderboard scoring)
_GRADE_SCORES = {"S": 10.0, "A": 8.0, "B": 6.0, "C": 4.0, "D": 2.0}


@router.get("/category-bests", response_model=CategoryBestsResponse)
async def get_category_bests(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryBestsResponse:
    """Get the authenticated user's best score per category_value.

    Queries rankings joined with rolls where category_value is not NULL,
    groups by category_value, and returns the best (highest grade) score
    for each category the user has played.

    Requirements: 6.5
    """
    # Fetch all rankings for this user that have a category_value
    result = await session.execute(
        select(Ranking.letter_grade, Roll.category_value)
        .join(Roll, Ranking.roll_id == Roll.id)
        .where(
            Ranking.user_id == current_user.id,
            Roll.category_value.isnot(None),
        )
    )
    rows = result.all()

    # Group by category_value and find the best score for each
    best_by_category: dict[str, float] = {}
    for letter_grade, category_value in rows:
        score = _GRADE_SCORES.get(letter_grade, 2.0)
        if category_value not in best_by_category or score > best_by_category[category_value]:
            best_by_category[category_value] = score

    entries = [
        CategoryBestEntry(category_value=cv, best_score=score)
        for cv, score in sorted(best_by_category.items())
    ]

    return CategoryBestsResponse(entries=entries)