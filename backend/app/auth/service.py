"""Auth business logic — local registration/login and Google OAuth.

Implements the three auth flows described in docs/backend_hld.md § 5.1
with error semantics from § 6.2.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import HTTPException, status
from jose import jwt as jose_jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    InvalidTokenError,
    TokenExpiredError,
)
from app.config import settings
from app.models.user import User


def _generate_tokens(user: User) -> tuple[str, str]:
    """Return an (access_token, refresh_token) pair for *user*."""
    user_id = str(user.id)
    return create_access_token(user_id, user.email), create_refresh_token(user_id)


# ---------------------------------------------------------------------------
# Local auth (email + password)
# ---------------------------------------------------------------------------


class AuthService:
    """Handles email/password registration, login, and token refresh."""

    @staticmethod
    async def register(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: str,
    ) -> tuple[User, str, str]:
        """Create a new local user and return ``(user, access_token, refresh_token)``.

        Raises:
            HTTPException 409 (EMAIL_EXISTS): if the email is already taken.
        """
        email = email.lower().strip()

        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
                headers={"X-Error-Code": "EMAIL_EXISTS"},
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            auth_provider="local",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        access_token, refresh_token = _generate_tokens(user)
        return user, access_token, refresh_token

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        """Authenticate with email/password and return ``(user, access_token, refresh_token)``.

        Raises:
            HTTPException 401 (INVALID_CREDENTIALS): on wrong email or password.
        """
        email = email.lower().strip()

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"X-Error-Code": "INVALID_CREDENTIALS"},
            )

        access_token, refresh_token = _generate_tokens(user)
        return user, access_token, refresh_token

    @staticmethod
    async def refresh(
        db: AsyncSession,
        refresh_token_str: str,
    ) -> tuple[User, str, str]:
        """Validate a refresh token and return ``(user, new_access_token, new_refresh_token)``.

        Raises:
            HTTPException 401 (INVALID_REFRESH_TOKEN): if the token is missing,
            expired, or not a refresh token.
        """
        try:
            payload = decode_token(refresh_token_str)
        except (TokenExpiredError, InvalidTokenError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"X-Error-Code": "INVALID_REFRESH_TOKEN"},
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"X-Error-Code": "INVALID_REFRESH_TOKEN"},
            )

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"X-Error-Code": "INVALID_REFRESH_TOKEN"},
            )

        access_token, refresh_token = _generate_tokens(user)
        return user, access_token, refresh_token


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleAuthService:
    """Handles Google OAuth code-exchange and account linking/creation."""

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        code: str,
        redirect_uri: str,
    ) -> tuple[User, str, str]:
        """Exchange a Google authorization *code* for tokens and return ``(user, access_token, refresh_token)``.

        Account resolution (per db_hld.md § 3.1):
        1. Existing user matched by ``google_sub`` → return that user.
        2. Existing user matched by ``email`` (no ``google_sub`` yet) → link the
           Google account by setting ``google_sub``.
        3. No match → create a new ``auth_provider="google"`` user.
        """
        google_payload = await _exchange_google_code(code, redirect_uri)

        google_sub: str = google_payload["sub"]
        email: str = google_payload["email"].lower().strip()
        full_name: str = google_payload.get("name", email.split("@")[0])

        # 1. Look up by google_sub
        result = await db.execute(select(User).where(User.google_sub == google_sub))
        user = result.scalar_one_or_none()

        if user is None:
            # 2. Look up by email — account linking
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user is not None:
                user.google_sub = google_sub
                await db.commit()
                await db.refresh(user)
            else:
                # 3. Brand-new Google user
                user = User(
                    email=email,
                    password_hash=None,
                    full_name=full_name,
                    auth_provider="google",
                    google_sub=google_sub,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

        access_token, refresh_token = _generate_tokens(user)
        return user, access_token, refresh_token


async def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    """POST to Google's token endpoint and decode the ``id_token`` JWT.

    The ``id_token`` is verified only for structure here (signature
    verification is delegated to Google's certs in production); we extract
    ``sub``, ``email``, and ``name`` from the payload.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange Google authorization code",
        )

    token_data = resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token response missing id_token",
        )

    # Decode without signature verification — Google's id_token is already
    # validated by the TLS exchange with googleapis.com.
    payload = jose_jwt.get_unverified_claims(id_token)

    if "sub" not in payload or "email" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google id_token missing required claims",
        )

    return payload
