"""Auth router — all authentication endpoints.

Implements the 6 auth endpoints defined in docs/backend_hld.md § 6.2.
Refresh tokens are stored in HttpOnly cookies; access tokens are returned
in the JSON response body.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from app.auth.service import AuthService, GoogleAuthService
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])

_REFRESH_COOKIE_KEY = "refresh_token"
_REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly cookie on *response*."""
    response.set_cookie(
        key=_REFRESH_COOKIE_KEY,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/auth",
        max_age=_REFRESH_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie from *response*."""
    response.delete_cookie(
        key=_REFRESH_COOKIE_KEY,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/auth",
    )


def _build_auth_response(
    user: User, access_token: str, refresh_token: str, response: Response
) -> AuthResponse:
    """Build an ``AuthResponse``, setting the refresh cookie as a side-effect."""
    _set_refresh_cookie(response, refresh_token)
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Create a new user account and return tokens."""
    user, access_token, refresh_token = await AuthService.register(
        db, body.email, body.password, body.full_name
    )
    return _build_auth_response(user, access_token, refresh_token, response)


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate with email and password."""
    user, access_token, refresh_token = await AuthService.login(
        db, body.email, body.password
    )
    return _build_auth_response(user, access_token, refresh_token, response)


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    body: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Exchange a Google authorization code for a session."""
    user, access_token, refresh_token = await GoogleAuthService.authenticate(
        db, body.code, body.redirect_uri
    )
    return _build_auth_response(user, access_token, refresh_token, response)


@router.post("/refresh", response_model=AuthResponse)
@limiter.exempt
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE_KEY),
) -> AuthResponse:
    """Obtain a new access token using the refresh token cookie.

    Returns the full user object so the frontend can restore session state
    after a page reload.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"X-Error-Code": "INVALID_REFRESH_TOKEN"},
        )

    user, new_access, new_refresh = await AuthService.refresh(db, refresh_token)
    return _build_auth_response(user, new_access, new_refresh, response)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
@limiter.exempt
async def logout(request: Request, response: Response) -> MessageResponse:
    """Invalidate the refresh token cookie."""
    _clear_refresh_cookie(response)
    return MessageResponse(detail="Logged out successfully")
