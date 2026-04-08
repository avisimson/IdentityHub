"""Authentication utilities — password hashing (bcrypt) and JWT management."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing — bcrypt with 12 rounds (per db_hld.md § 5.3)
# ---------------------------------------------------------------------------
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password* using 12 rounds."""
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify *plain* against a bcrypt *hashed* value."""
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers — HS256, signed with settings.SECRET_KEY
# ---------------------------------------------------------------------------
_ALGORITHM = "HS256"


class TokenExpiredError(Exception):
    """Raised when a JWT has expired."""


class InvalidTokenError(Exception):
    """Raised when a JWT is malformed or its signature is invalid."""


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token (default 15 min).

    Payload: sub (user_id), email, exp, type="access".
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token (default 7 days).

    Payload: sub (user_id), exp, type="refresh".
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.

    Returns the full payload dict on success.

    Raises:
        TokenExpiredError: if the token has expired.
        InvalidTokenError: if the token is malformed or the signature fails.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        return payload
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise TokenExpiredError("Token has expired") from exc
        raise InvalidTokenError("Invalid or malformed token") from exc
