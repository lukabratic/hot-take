"""Clerk JWT verification middleware for FastAPI."""

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_session
from models import User

security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)

# Cache for JWKS keys to avoid fetching on every request
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch and cache JWKS keys from Clerk."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        response = await client.get(settings.clerk_jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def _decode_clerk_jwt(token: str) -> dict:
    """Decode and verify a Clerk-issued JWT.

    Uses the configured issuer for validation. Fetches JWKS from Clerk
    for signature verification when configured.
    """
    try:
        if settings.clerk_jwks_url:
            jwks = await _get_jwks()
            payload = jwt.decode(
                token,
                key=jwks,
                algorithms=["RS256"],
                issuer=settings.clerk_issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_iss": bool(settings.clerk_issuer),
                },
            )
        else:
            # Development mode: decode without signature verification
            payload = jwt.decode(
                token,
                key="",
                algorithms=["RS256"],
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
            if settings.clerk_issuer and payload.get("iss") != settings.clerk_issuer:
                raise JWTError("Invalid issuer")

        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to verify token: could not reach auth provider",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """FastAPI dependency that verifies Clerk JWT and returns the authenticated user.

    Raises 401 if the token is invalid or the user doesn't exist in the database.
    """
    payload = await _decode_clerk_jwt(credentials.credentials)

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(User).where(User.clerk_id == clerk_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please sync your account first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_security)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User | None:
    """FastAPI dependency that optionally returns a user if a valid JWT is provided.

    Returns None if no token is provided. Raises 401 only if a token is
    provided but invalid.
    """
    if credentials is None:
        return None

    payload = await _decode_clerk_jwt(credentials.credentials)

    clerk_id = payload.get("sub")
    if not clerk_id:
        return None

    result = await session.execute(
        select(User).where(User.clerk_id == clerk_id)
    )
    return result.scalar_one_or_none()
