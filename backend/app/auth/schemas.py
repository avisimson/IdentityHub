"""Pydantic request/response schemas for the auth domain.

Matches the API contract defined in docs/backend_hld.md § 6.2.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """POST /auth/register request body."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """POST /auth/google request body."""

    code: str
    redirect_uri: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Serialised user object returned inside auth responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    auth_provider: str


class AuthResponse(BaseModel):
    """Successful authentication response (register / login / google / refresh)."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic success message (e.g. logout confirmation)."""

    detail: str


class ErrorResponse(BaseModel):
    """Structured error body returned on 4xx failures."""

    detail: str
    code: str
