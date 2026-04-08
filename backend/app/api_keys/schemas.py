"""Pydantic request/response schemas for the API-key domain.

Matches the API contract defined in docs/backend_hld.md § 6.4.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateApiKeyRequest(BaseModel):
    """POST /api-keys request body."""

    name: str = Field(min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ApiKeyCreatedResponse(BaseModel):
    """Returned once at creation time — the only time the raw key is visible."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key: str
    created_at: datetime


class ApiKeyListItem(BaseModel):
    """Single API key in a listing (raw key is never exposed)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None


class ApiKeysListResponse(BaseModel):
    """GET /api-keys response envelope."""

    api_keys: list[ApiKeyListItem]


class ApiKeyRevealResponse(BaseModel):
    """GET /api-keys/{id}/reveal — returns the full decrypted key."""

    key: str
