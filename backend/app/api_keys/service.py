"""API-key business logic — generate, list, revoke, validate.

Security model from docs/db_hld.md § 3.3 and § 5.2:
- Raw key = ``ihub_live_`` + 48 random hex chars.
- Only the SHA-256 hash is persisted; the raw key is returned once.
- ``key_prefix`` stores the first 12 characters for UI display.
- Revocation is a soft-delete (``is_active = False``).
- Validation distinguishes ``INVALID_API_KEY`` from ``API_KEY_REVOKED``.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jira.encryption import encrypt_token, decrypt_token
from app.models.api_key import ApiKey
from app.models.user import User

_KEY_PREFIX_LENGTH = 12
_KEY_RANDOM_HEX_LENGTH = 48


def _generate_raw_key() -> str:
    """Return a new raw API key: ``ihub_live_`` + 48 random hex chars."""
    return f"ihub_live_{secrets.token_hex(_KEY_RANDOM_HEX_LENGTH // 2)}"


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of *raw_key*."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


class ApiKeyService:
    """CRUD + validation operations on API keys."""

    @staticmethod
    async def generate_key(
        user_id: uuid.UUID,
        name: str,
        db: AsyncSession,
    ) -> tuple[ApiKey, str]:
        """Create a new API key and return ``(api_key_row, raw_key)``.

        The raw key is available only through this return value — it is
        never stored in the database.
        """
        raw_key = _generate_raw_key()
        key_hash = _hash_key(raw_key)
        key_prefix = raw_key[:_KEY_PREFIX_LENGTH]

        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            encrypted_key=encrypt_token(raw_key),
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key, raw_key

    @staticmethod
    async def list_keys(
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> list[ApiKey]:
        """Return all **active** API keys belonging to *user_id*."""
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke_key(
        user_id: uuid.UUID,
        key_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete an API key by setting ``is_active = False``.

        Raises:
            HTTPException 404: if the key does not exist or does not
                belong to the requesting user.
        """
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
                headers={"X-Error-Code": "API_KEY_NOT_FOUND"},
            )

        api_key.is_active = False
        await db.commit()

    @staticmethod
    async def reveal_key(
        user_id: uuid.UUID,
        key_id: uuid.UUID,
        db: AsyncSession,
    ) -> str:
        """Decrypt and return the full raw API key."""
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
                ApiKey.is_active.is_(True),
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        if api_key.encrypted_key is None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Full key is not available for keys created before this feature",
            )

        return decrypt_token(api_key.encrypted_key)

    @staticmethod
    async def validate_api_key(
        raw_key: str,
        db: AsyncSession,
    ) -> tuple[ApiKey, User]:
        """Authenticate a raw API key and return ``(api_key, user)``.

        Error semantics (per db_hld.md § 3.3):
        - Key hash not found → ``INVALID_API_KEY`` (401).
        - Key found but ``is_active = False`` → ``API_KEY_REVOKED`` (401).

        On success the key's ``last_used_at`` timestamp is updated.
        """
        key_hash = _hash_key(raw_key)

        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"X-Error-Code": "INVALID_API_KEY"},
            )

        if not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
                headers={"X-Error-Code": "API_KEY_REVOKED"},
            )

        api_key.last_used_at = datetime.now(timezone.utc)
        await db.commit()

        # Eagerly load the owning user
        await db.refresh(api_key, ["user"])

        return api_key, api_key.user
