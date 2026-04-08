"""Rate limiting configuration — slowapi.

Provides the shared ``limiter`` instance used by main.py and individual
routers.  Kept in a separate module to avoid circular imports (main.py
imports routers, and routers may reference the limiter).

Limits per docs/backend_hld.md § 7:
  - Authenticated endpoints: 60 req/min per user (default)
  - External API: 20 req/min per API key (applied at the route level)
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_user_key(request: Request) -> str:
    """Extract a rate-limit key from the authenticated user's JWT.

    Falls back to the client IP when no valid Bearer token is present
    (e.g. unauthenticated endpoints like /auth/login).
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            from app.auth.utils import decode_token

            payload = decode_token(token)
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)


def get_api_key_or_ip(request: Request) -> str:
    """Rate-limit key for the external API — keyed by the raw API key value.

    Falls back to client IP when no ``X-API-Key`` header is supplied.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_key, default_limits=["60/minute"])
