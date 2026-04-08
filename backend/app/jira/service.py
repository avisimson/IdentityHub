"""JiraService — OAuth flow, token management, and Jira Cloud API calls.

Implements the full Jira integration per docs/backend_hld.md §5.2 (OAuth 3LO)
and §6.3 (endpoint behaviours).  Tokens are Fernet-encrypted at rest (see
docs/db_hld.md §5.1) and only decrypted in-memory for API calls.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.jira.encryption import decrypt_token, encrypt_token
from app.jira.schemas import (
    CreateTicketRequest,
    JiraIssueType,
    JiraProject,
    JiraStatusResponse,
    TicketCreatedBy,
    TicketResponse,
)
from app.models.jira_connection import JiraConnection
from app.models.ticket import Ticket
from app.models.user import User

logger = logging.getLogger(__name__)

_ATLASSIAN_AUTH_URL = "https://auth.atlassian.com/authorize"
_ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
_ATLASSIAN_RESOURCES_URL = (
    "https://api.atlassian.com/oauth/token/accessible-resources"
)
_JIRA_SCOPES = "read:jira-work write:jira-work offline_access"

_STATE_SEPARATOR = ":"


class JiraOAuthError(Exception):
    """Raised when the Jira OAuth flow fails."""


class JiraAPIError(Exception):
    """Raised when an upstream Jira API call fails."""


class JiraNotConnectedError(Exception):
    """Raised when the user has no active Jira connection."""


class JiraService:
    """Stateless service with class-methods for Jira integration."""

    # ------------------------------------------------------------------
    # 1. generate_auth_url
    # ------------------------------------------------------------------

    @staticmethod
    def generate_auth_url(user_id: str) -> tuple[str, str]:
        """Build the Atlassian OAuth authorization URL.

        The ``state`` parameter is HMAC-signed so the callback can
        identify the user without a Bearer token (per HLD §5.2).

        Returns:
            (authorization_url, state)
        """
        nonce = secrets.token_hex(16)
        payload = f"{user_id}{_STATE_SEPARATOR}{nonce}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        state = f"{payload}{_STATE_SEPARATOR}{signature}"

        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.JIRA_CLIENT_ID,
            "scope": _JIRA_SCOPES,
            "redirect_uri": settings.JIRA_REDIRECT_URI,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
        authorization_url = f"{_ATLASSIAN_AUTH_URL}?{urlencode(params)}"
        return authorization_url, state

    # ------------------------------------------------------------------
    # 2. handle_callback
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_callback(
        code: str, state: str, db: AsyncSession
    ) -> None:
        """Exchange the authorization code for tokens and persist them.

        Verifies the HMAC-signed ``state``, fetches tokens and cloud
        resources, encrypts tokens, and upserts into ``jira_connections``.
        """
        user_id = JiraService._verify_state(state)

        async with httpx.AsyncClient() as client:
            token_data = await JiraService._exchange_code(client, code)

            access_token: str = token_data["access_token"]
            refresh_token: str = token_data["refresh_token"]
            expires_in: int = token_data.get("expires_in", 3600)

            cloud_id, site_url = await JiraService._fetch_cloud_info(
                client, access_token
            )

        token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in
        )

        result = await db.execute(
            select(JiraConnection).where(
                JiraConnection.user_id == uuid.UUID(user_id)
            )
        )
        connection = result.scalar_one_or_none()

        if connection is None:
            connection = JiraConnection(
                user_id=uuid.UUID(user_id),
                cloud_id=cloud_id,
                site_url=site_url,
                access_token_enc=encrypt_token(access_token),
                refresh_token_enc=encrypt_token(refresh_token),
                token_expires_at=token_expires_at,
            )
            db.add(connection)
        else:
            connection.cloud_id = cloud_id
            connection.site_url = site_url
            connection.access_token_enc = encrypt_token(access_token)
            connection.refresh_token_enc = encrypt_token(refresh_token)
            connection.token_expires_at = token_expires_at

        await db.commit()

    # ------------------------------------------------------------------
    # 3. get_status
    # ------------------------------------------------------------------

    @staticmethod
    async def get_status(
        user_id: str, db: AsyncSession
    ) -> JiraStatusResponse:
        """Return connection status — always 200 per HLD §6.3."""
        connection = await JiraService._get_connection_or_none(user_id, db)
        if connection is None:
            return JiraStatusResponse(connected=False)
        return JiraStatusResponse(
            connected=True,
            cloud_id=connection.cloud_id,
            jira_site_url=connection.site_url,
        )

    # ------------------------------------------------------------------
    # 4. get_projects
    # ------------------------------------------------------------------

    @staticmethod
    async def get_projects(
        user_id: str, db: AsyncSession
    ) -> list[JiraProject]:
        """List accessible Jira projects for the connected user."""
        connection = await JiraService._require_connection(user_id, db)
        data = await JiraService._make_jira_request(
            "GET",
            f"https://api.atlassian.com/ex/jira/{connection.cloud_id}"
            "/rest/api/3/project",
            connection,
            db,
        )
        return [
            JiraProject(
                id=str(p["id"]),
                key=p["key"],
                name=p["name"],
                avatar_url=(p.get("avatarUrls") or {}).get("48x48"),
            )
            for p in data
        ]

    # ------------------------------------------------------------------
    # 5. get_issue_types
    # ------------------------------------------------------------------

    @staticmethod
    async def get_issue_types(
        user_id: str, project_key: str, db: AsyncSession
    ) -> list[JiraIssueType]:
        """List available issue types for a project."""
        connection = await JiraService._require_connection(user_id, db)
        data = await JiraService._make_jira_request(
            "GET",
            f"https://api.atlassian.com/ex/jira/{connection.cloud_id}"
            f"/rest/api/3/project/{project_key}",
            connection,
            db,
        )
        issue_types_raw = data.get("issueTypes", [])
        return [
            JiraIssueType(
                id=str(it["id"]),
                name=it["name"],
                is_default=it.get("untranslatedName", "") == "Task",
            )
            for it in issue_types_raw
        ]

    # ------------------------------------------------------------------
    # 6. create_ticket
    # ------------------------------------------------------------------

    @staticmethod
    async def create_ticket(
        user_id: str,
        payload: CreateTicketRequest,
        source: str,
        db: AsyncSession,
    ) -> TicketResponse:
        """Create a Jira ticket and persist a local record.

        ``source`` is one of ``"ui"``, ``"api"``, or ``"blog_digest"``.
        """
        connection = await JiraService._require_connection(user_id, db)

        fields: dict = {
            "project": {"key": payload.project_key},
            "summary": payload.summary,
            "issuetype": {"name": payload.issue_type},
        }
        if payload.description:
            fields["description"] = {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": payload.description}
                        ],
                    }
                ],
            }

        jira_data = await JiraService._make_jira_request(
            "POST",
            f"https://api.atlassian.com/ex/jira/{connection.cloud_id}"
            "/rest/api/3/issue",
            connection,
            db,
            json={"fields": fields},
        )

        jira_key: str = jira_data["key"]
        jira_url = f"{connection.site_url}/browse/{jira_key}"

        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one()

        ticket = Ticket(
            user_id=uuid.UUID(user_id),
            jira_connection_id=connection.id,
            jira_ticket_key=jira_key,
            jira_ticket_url=jira_url,
            project_key=payload.project_key,
            summary=payload.summary,
            description=payload.description,
            issue_type=payload.issue_type,
            source=source,
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

        return TicketResponse(
            id=ticket.id,
            jira_ticket_key=ticket.jira_ticket_key,
            jira_ticket_url=ticket.jira_ticket_url,
            summary=ticket.summary,
            issue_type=ticket.issue_type,
            source=ticket.source,
            created_at=ticket.created_at,
            created_by=TicketCreatedBy(
                id=user.id,
                full_name=user.full_name,
            ),
        )

    # ------------------------------------------------------------------
    # 7. get_recent_tickets
    # ------------------------------------------------------------------

    @staticmethod
    async def get_recent_tickets(
        project_key: str, limit: int, db: AsyncSession
    ) -> list[TicketResponse]:
        """Query local ``tickets`` table per db_hld §3.4 pattern.

        Joined with ``users`` to populate ``created_by``.  Ordered by
        ``created_at DESC`` and capped at *limit* (max 50).
        """
        capped_limit = min(limit, 50)
        result = await db.execute(
            select(Ticket, User)
            .join(User, Ticket.user_id == User.id)
            .where(Ticket.project_key == project_key)
            .order_by(Ticket.created_at.desc())
            .limit(capped_limit)
        )
        rows = result.all()
        return [
            TicketResponse(
                id=ticket.id,
                jira_ticket_key=ticket.jira_ticket_key,
                jira_ticket_url=ticket.jira_ticket_url,
                summary=ticket.summary,
                issue_type=ticket.issue_type,
                source=ticket.source,
                created_at=ticket.created_at,
                created_by=TicketCreatedBy(
                    id=user.id,
                    full_name=user.full_name,
                ),
            )
            for ticket, user in rows
        ]

    # ------------------------------------------------------------------
    # 8. disconnect
    # ------------------------------------------------------------------

    @staticmethod
    async def disconnect(user_id: str, db: AsyncSession) -> None:
        """Delete the user's Jira connection and all associated tickets."""
        uid = uuid.UUID(user_id)
        result = await db.execute(
            select(JiraConnection).where(JiraConnection.user_id == uid)
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            return

        # Delete tickets that reference this connection first to avoid FK violations.
        ticket_result = await db.execute(
            select(Ticket).where(Ticket.jira_connection_id == connection.id)
        )
        for ticket in ticket_result.scalars().all():
            await db.delete(ticket)

        await db.delete(connection)
        await db.commit()

    # ------------------------------------------------------------------
    # 9. _refresh_token  (private)
    # ------------------------------------------------------------------

    @staticmethod
    async def _refresh_token(
        connection: JiraConnection, db: AsyncSession
    ) -> str:
        """Use the refresh token to obtain a new access token.

        Re-encrypts and persists both new tokens.  Returns the new
        plaintext access token.
        """
        refresh_tok = decrypt_token(connection.refresh_token_enc)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _ATLASSIAN_TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "client_id": settings.JIRA_CLIENT_ID,
                    "client_secret": settings.JIRA_CLIENT_SECRET,
                    "refresh_token": refresh_tok,
                },
            )

        if resp.status_code != 200:
            logger.error("Token refresh failed: %s %s", resp.status_code, resp.text)
            raise JiraAPIError(f"Token refresh failed ({resp.status_code})")

        data = resp.json()
        new_access = data["access_token"]
        new_refresh = data.get("refresh_token", refresh_tok)
        expires_in = data.get("expires_in", 3600)

        connection.access_token_enc = encrypt_token(new_access)
        connection.refresh_token_enc = encrypt_token(new_refresh)
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in
        )
        await db.commit()

        return new_access

    # ------------------------------------------------------------------
    # 10. _make_jira_request  (private)
    # ------------------------------------------------------------------

    @staticmethod
    async def _make_jira_request(
        method: str,
        url: str,
        connection: JiraConnection,
        db: AsyncSession,
        **kwargs,
    ) -> dict | list:
        """Make an authenticated Jira API request.

        On HTTP 401 the token is refreshed and the request retried once
        (single-retry pattern per HLD §5.2).
        """
        access_token = decrypt_token(connection.access_token_enc)

        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                **kwargs,
            )

            if resp.status_code == 401:
                logger.info("Jira 401 — attempting token refresh")
                new_token = await JiraService._refresh_token(connection, db)
                resp = await client.request(
                    method,
                    url,
                    headers={
                        "Authorization": f"Bearer {new_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    **kwargs,
                )

            if resp.status_code >= 400:
                logger.error(
                    "Jira API error: %s %s — %s",
                    method,
                    url,
                    resp.text,
                )
                raise JiraAPIError(
                    f"Jira API error: {resp.status_code} — {resp.text[:200]}"
                )

        return resp.json()

    # ==================================================================
    # Internal helpers
    # ==================================================================

    @staticmethod
    def _verify_state(state: str) -> str:
        """Verify the HMAC-signed OAuth state and extract the ``user_id``.

        State format: ``{user_id}:{nonce}:{signature}``

        Raises ``JiraOAuthError`` on invalid or tampered state.
        """
        parts = state.rsplit(_STATE_SEPARATOR, maxsplit=1)
        if len(parts) != 2:
            raise JiraOAuthError("Invalid OAuth state format")

        payload, received_sig = parts
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, received_sig):
            raise JiraOAuthError("Invalid OAuth state signature")

        user_id = payload.split(_STATE_SEPARATOR, maxsplit=1)[0]
        return user_id

    @staticmethod
    async def _exchange_code(
        client: httpx.AsyncClient, code: str
    ) -> dict:
        """Exchange an authorization code for OAuth tokens."""
        resp = await client.post(
            _ATLASSIAN_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": settings.JIRA_CLIENT_ID,
                "client_secret": settings.JIRA_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.JIRA_REDIRECT_URI,
            },
        )
        if resp.status_code != 200:
            logger.error("Code exchange failed: %s %s", resp.status_code, resp.text)
            raise JiraOAuthError(
                f"Failed to exchange authorization code ({resp.status_code})"
            )
        return resp.json()

    @staticmethod
    async def _fetch_cloud_info(
        client: httpx.AsyncClient, access_token: str
    ) -> tuple[str, str]:
        """Fetch the Jira Cloud ``cloud_id`` and site URL."""
        resp = await client.get(
            _ATLASSIAN_RESOURCES_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            raise JiraOAuthError("Failed to fetch accessible resources")

        resources = resp.json()
        if not resources:
            raise JiraOAuthError("No accessible Jira sites found")

        site = resources[0]
        return site["id"], site["url"]

    @staticmethod
    async def _get_connection_or_none(
        user_id: str, db: AsyncSession
    ) -> JiraConnection | None:
        """Load the Jira connection for a user, or ``None``."""
        result = await db.execute(
            select(JiraConnection).where(
                JiraConnection.user_id == uuid.UUID(user_id)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _require_connection(
        user_id: str, db: AsyncSession
    ) -> JiraConnection:
        """Load the Jira connection or raise ``JiraNotConnectedError``."""
        connection = await JiraService._get_connection_or_none(user_id, db)
        if connection is None:
            raise JiraNotConnectedError("Jira not connected")
        return connection
