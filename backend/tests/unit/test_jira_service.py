"""Unit tests for app/jira/service.py — JiraService core logic.

Tests per docs/backend_hld.md § 5.2 (OAuth 3LO), § 6.3 (Endpoint behaviour),
and docs/db_hld.md §§ 3.2, 3.4.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.jira.service import JiraAPIError, JiraOAuthError, JiraService
from app.models.jira_connection import JiraConnection
from app.models.ticket import Ticket
from app.models.user import User


_TEST_SECRET = "test-secret-key-0123456789abcdef0123456789abcdef"
_TEST_FERNET_KEY = Fernet.generate_key()


def _make_test_settings():
    from app.config import Settings
    return Settings(
        DATABASE_URL="sqlite+aiosqlite://",
        SECRET_KEY=_TEST_SECRET,
        JIRA_ENCRYPTION_KEY=_TEST_FERNET_KEY.decode(),
        JIRA_CLIENT_ID="test-client-id",
        JIRA_CLIENT_SECRET="test-client-secret",
        JIRA_REDIRECT_URI="http://localhost:8000/jira/auth/callback",
    )


_settings = _make_test_settings()
_fernet = Fernet(_TEST_FERNET_KEY)


@pytest.fixture(autouse=True)
def _patch_settings():
    with patch("app.jira.service.settings", _settings), \
         patch("app.jira.encryption.settings", _settings), \
         patch("app.jira.encryption._fernet", _fernet):
        yield


# ── OAuth State ────────────────────────────────────────────────────────────


class TestOAuthState:
    def test_generate_auth_url_includes_state_with_hmac(self):
        url, state = JiraService.generate_auth_url("user-1")
        assert "state=" in url
        assert len(state) > 0

    def test_state_hmac_verifies_on_callback(self):
        _, state = JiraService.generate_auth_url("user-42")
        extracted_user_id = JiraService._verify_state(state)
        assert extracted_user_id == "user-42"

    def test_state_hmac_rejects_tampered_state(self):
        _, state = JiraService.generate_auth_url("user-42")
        tampered = state[:-4] + "XXXX"
        with pytest.raises(JiraOAuthError):
            JiraService._verify_state(tampered)

    def test_generate_auth_url_contains_correct_scopes(self):
        url, _ = JiraService.generate_auth_url("user-1")
        assert "read%3Ajira-work" in url or "read:jira-work" in url
        assert "write%3Ajira-work" in url or "write:jira-work" in url
        assert "offline_access" in url


# ── Jira Status ────────────────────────────────────────────────────────────


class TestJiraStatus:
    async def test_get_status_connected_returns_true(self, db_session, test_user):
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="cloud-abc",
            site_url="https://test.atlassian.net",
            access_token_enc=_fernet.encrypt(b"at"),
            refresh_token_enc=_fernet.encrypt(b"rt"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        status = await JiraService.get_status(str(user.id), db_session)
        assert status.connected is True
        assert status.cloud_id == "cloud-abc"
        assert status.jira_site_url == "https://test.atlassian.net"

    async def test_get_status_not_connected_returns_false(self, db_session, test_user):
        user = await test_user()
        status = await JiraService.get_status(str(user.id), db_session)
        assert status.connected is False


# ── Token Refresh (single retry on 401) ────────────────────────────────────


class TestMakeJiraRequest:
    async def test_make_jira_request_retries_on_401(self, db_session, test_user):
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="cloud-retry",
            site_url="https://retry.atlassian.net",
            access_token_enc=_fernet.encrypt(b"old-token"),
            refresh_token_enc=_fernet.encrypt(b"refresh-token"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        resp_401 = MagicMock(status_code=401, text="Unauthorized")
        resp_200 = MagicMock(status_code=200, text='{}')
        resp_200.json.return_value = {"ok": True}

        refresh_resp = MagicMock(status_code=200)
        refresh_resp.json.return_value = {
            "access_token": "new-at",
            "refresh_token": "new-rt",
            "expires_in": 3600,
        }

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=[resp_401, resp_200])
        mock_client.post = AsyncMock(return_value=refresh_resp)

        with patch("app.jira.service.httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("app.jira.service.JiraService._refresh_token", new_callable=AsyncMock) as mock_refresh:
                mock_refresh.return_value = "new-access-token"

                result = await JiraService._make_jira_request(
                    "GET", "https://api.atlassian.com/test", conn, db_session
                )

            mock_refresh.assert_called_once()
            assert result == {"ok": True}

    async def test_make_jira_request_fails_after_retry_exhausted(self, db_session, test_user):
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="cloud-fail",
            site_url="https://fail.atlassian.net",
            access_token_enc=_fernet.encrypt(b"old-token"),
            refresh_token_enc=_fernet.encrypt(b"refresh-token"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        resp_401 = MagicMock(status_code=401, text="Unauthorized")

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=resp_401)

        with patch("app.jira.service.httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("app.jira.service.JiraService._refresh_token", new_callable=AsyncMock) as mock_refresh:
                mock_refresh.return_value = "new-access-token"

                with pytest.raises(JiraAPIError):
                    await JiraService._make_jira_request(
                        "GET", "https://api.atlassian.com/test", conn, db_session
                    )


# ── Ticket Creation ────────────────────────────────────────────────────────


class TestCreateTicket:
    async def _setup_connection(self, db_session, user):
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="cloud-tkt",
            site_url="https://tkt.atlassian.net",
            access_token_enc=_fernet.encrypt(b"at"),
            refresh_token_enc=_fernet.encrypt(b"rt"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()
        return conn

    async def test_create_ticket_records_in_local_db(self, db_session, test_user):
        from app.jira.schemas import CreateTicketRequest

        user = await test_user()
        await self._setup_connection(db_session, user)

        jira_resp = {"key": "PROJ-42", "id": "12345"}

        with patch.object(
            JiraService, "_make_jira_request", new_callable=AsyncMock, return_value=jira_resp
        ):
            req = CreateTicketRequest(
                project_key="PROJ", summary="Test ticket", issue_type="Task"
            )
            result = await JiraService.create_ticket(str(user.id), req, "ui", db_session)

        assert result.jira_ticket_key == "PROJ-42"
        assert result.summary == "Test ticket"

        from sqlalchemy import select
        rows = (await db_session.execute(select(Ticket))).scalars().all()
        assert len(rows) == 1
        assert rows[0].project_key == "PROJ"

    async def test_create_ticket_sets_source_correctly(self, db_session, test_user):
        from app.jira.schemas import CreateTicketRequest

        for source_val in ("ui", "api", "blog_digest"):
            user = await test_user()
            await self._setup_connection(db_session, user)

            jira_resp = {"key": f"SRC-{source_val[:2].upper()}", "id": "99"}
            with patch.object(
                JiraService, "_make_jira_request", new_callable=AsyncMock, return_value=jira_resp
            ):
                req = CreateTicketRequest(
                    project_key="SRC", summary=f"Source test {source_val}", issue_type="Task"
                )
                result = await JiraService.create_ticket(str(user.id), req, source_val, db_session)

            assert result.source == source_val


# ── Recent Tickets ─────────────────────────────────────────────────────────


class TestRecentTickets:
    async def _create_ticket(self, db_session, user, conn, key, project="PROJ", offset_hours=0):
        from datetime import timedelta
        t = Ticket(
            user_id=user.id,
            jira_connection_id=conn.id,
            jira_ticket_key=key,
            jira_ticket_url=f"https://x.atlassian.net/browse/{key}",
            project_key=project,
            summary=f"Summary for {key}",
            issue_type="Task",
            source="ui",
        )
        db_session.add(t)
        await db_session.commit()
        return t

    async def _setup(self, db_session, test_user):
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="c",
            site_url="https://x.atlassian.net",
            access_token_enc=_fernet.encrypt(b"a"),
            refresh_token_enc=_fernet.encrypt(b"r"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()
        return user, conn

    async def test_get_recent_tickets_orders_by_created_at_desc(self, db_session, test_user):
        user, conn = await self._setup(db_session, test_user)
        await self._create_ticket(db_session, user, conn, "P-1")
        await self._create_ticket(db_session, user, conn, "P-2")
        await self._create_ticket(db_session, user, conn, "P-3")

        tickets = await JiraService.get_recent_tickets("PROJ", 10, db_session)
        keys = [t.jira_ticket_key for t in tickets]
        assert keys == ["P-3", "P-2", "P-1"]

    async def test_get_recent_tickets_filters_by_project_key(self, db_session, test_user):
        user, conn = await self._setup(db_session, test_user)
        await self._create_ticket(db_session, user, conn, "A-1", project="ALPHA")
        await self._create_ticket(db_session, user, conn, "B-1", project="BETA")

        alpha_tickets = await JiraService.get_recent_tickets("ALPHA", 10, db_session)
        assert len(alpha_tickets) == 1
        assert alpha_tickets[0].jira_ticket_key == "A-1"

    async def test_get_recent_tickets_respects_limit(self, db_session, test_user):
        user, conn = await self._setup(db_session, test_user)
        for i in range(15):
            await self._create_ticket(db_session, user, conn, f"L-{i}")

        tickets = await JiraService.get_recent_tickets("PROJ", 10, db_session)
        assert len(tickets) == 10


# ── Disconnect ─────────────────────────────────────────────────────────────


class TestDisconnect:
    async def test_disconnect_deletes_jira_connection(self, db_session, test_user):
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="c",
            site_url="https://x.atlassian.net",
            access_token_enc=_fernet.encrypt(b"a"),
            refresh_token_enc=_fernet.encrypt(b"r"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.commit()

        await JiraService.disconnect(str(user.id), db_session)

        from sqlalchemy import select
        result = await db_session.execute(
            select(JiraConnection).where(JiraConnection.user_id == user.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_disconnect_deletes_connection_with_tickets(self, db_session, test_user):
        """Disconnecting must also remove associated tickets (FK integrity)."""
        user = await test_user()
        conn = JiraConnection(
            user_id=user.id,
            cloud_id="c",
            site_url="https://x.atlassian.net",
            access_token_enc=_fernet.encrypt(b"a"),
            refresh_token_enc=_fernet.encrypt(b"r"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(conn)
        await db_session.flush()

        ticket = Ticket(
            user_id=user.id,
            jira_connection_id=conn.id,
            jira_ticket_key="PROJ-1",
            jira_ticket_url="https://x.atlassian.net/browse/PROJ-1",
            project_key="PROJ",
            summary="Test ticket",
            source="manual",
        )
        db_session.add(ticket)
        await db_session.commit()

        await JiraService.disconnect(str(user.id), db_session)

        from sqlalchemy import select
        conn_result = await db_session.execute(
            select(JiraConnection).where(JiraConnection.user_id == user.id)
        )
        assert conn_result.scalar_one_or_none() is None

        ticket_result = await db_session.execute(
            select(Ticket).where(Ticket.user_id == user.id)
        )
        assert ticket_result.scalar_one_or_none() is None

    async def test_disconnect_noop_when_not_connected(self, db_session, test_user):
        """Disconnecting a user with no connection should not raise."""
        user = await test_user()
        await JiraService.disconnect(str(user.id), db_session)
