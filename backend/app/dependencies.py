"""Shared FastAPI dependencies.

``get_db`` — async database session.
``get_current_user`` — JWT-authenticated user (Bearer token).
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import InvalidTokenError, TokenExpiredError, decode_token
from app.database import get_db
from app.models.user import User

__all__ = ["get_db", "get_current_user"]

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the Bearer access token, then load the user.

    Raises ``401 NOT_AUTHENTICATED`` when the token is missing, expired,
    malformed, not an access token, or references a non-existent user.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"X-Error-Code": "NOT_AUTHENTICATED"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except (TokenExpiredError, InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"X-Error-Code": "NOT_AUTHENTICATED"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"X-Error-Code": "NOT_AUTHENTICATED"},
        )

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"X-Error-Code": "NOT_AUTHENTICATED"},
        )

    return user
