"""Centralised application exceptions.

Every custom exception that needs a global handler lives here.
Router / service layers should raise these instead of ``HTTPException``
so the global handlers in ``main.py`` can translate them into the
project's ``{"detail": "…", "code": "…"}`` error envelope.
"""


class AuthenticationError(Exception):
    """Credentials are missing, expired, or invalid (→ 401)."""


class JiraNotConnectedError(Exception):
    """The user has no active Jira OAuth connection (→ 403)."""


class JiraApiError(Exception):
    """An upstream Jira Cloud API call failed (→ 502)."""
