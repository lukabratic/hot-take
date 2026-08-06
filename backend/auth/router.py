"""Authentication router for user sync and profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from database import get_session
from models import User
from schemas import UserProfileResponse, UserSyncRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/sync", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def sync_user(
    request: UserSyncRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Create or update a user from Clerk claims.

    Called by the frontend after Clerk authentication to ensure the user
    exists in the database. If the user already exists (matched by clerk_id),
    their profile fields are updated. Otherwise a new user record is created.
    """
    result = await session.execute(
        select(User).where(User.clerk_id == request.clerk_id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        # Update existing user fields
        user.username = request.username
        if request.email is not None:
            user.email = request.email
        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url
    else:
        # Check username uniqueness before creating
        existing_username = await session.execute(
            select(User).where(User.username == request.username)
        )
        if existing_username.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        user = User(
            clerk_id=request.clerk_id,
            username=request.username,
            email=request.email,
            avatar_url=request.avatar_url,
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the authenticated user's profile."""
    return current_user
