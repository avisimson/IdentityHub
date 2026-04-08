"""API Key management router — create, list, revoke.

Implements the three endpoints defined in docs/backend_hld.md § 6.4.
All endpoints require Bearer authentication via ``get_current_user``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys.schemas import (
    ApiKeyCreatedResponse,
    ApiKeysListResponse,
    ApiKeyListItem,
    CreateApiKeyRequest,
)
from app.api_keys.service import ApiKeyService
from app.auth.schemas import MessageResponse
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    """Generate a new API key for the authenticated user.

    The raw key value is returned **only** in this response and is never
    stored or retrievable again.
    """
    api_key, raw_key = await ApiKeyService.generate_key(
        user_id=current_user.id,
        name=body.name,
        db=db,
    )
    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        created_at=api_key.created_at,
    )


@router.get("", response_model=ApiKeysListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeysListResponse:
    """List all active API keys for the authenticated user.

    Key values are masked — only the prefix is returned.
    """
    keys = await ApiKeyService.list_keys(user_id=current_user.id, db=db)
    return ApiKeysListResponse(
        api_keys=[
            ApiKeyListItem(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
            )
            for k in keys
        ]
    )


@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke an API key (soft-delete).

    Sets ``is_active = False`` rather than deleting the row, preserving
    an audit trail.
    """
    await ApiKeyService.revoke_key(
        user_id=current_user.id,
        key_id=key_id,
        db=db,
    )
    return MessageResponse(detail="API key revoked")
