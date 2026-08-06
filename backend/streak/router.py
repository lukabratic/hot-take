"""Streak tracking API endpoints.

Provides the GET /api/streak endpoint and the streak update logic
that integrates with ranking submission for daily mode.

Requirements: 11.1, 11.2, 11.4
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from database import get_session
from models import User
from schemas import StreakResponse

router = APIRouter(prefix="/api", tags=["streak"])


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreakResponse:
    """Get the authenticated user's current streak data.

    Returns the current streak count and longest streak.
    """
    return StreakResponse(
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
    )
