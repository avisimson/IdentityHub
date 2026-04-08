"""Integration tests for all Jira API endpoints.

Tests per docs/backend_hld.md § 6.3 — all contracts and error codes.
Mock all external Atlassian/Jira API calls.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.models.jira_connection import JiraConnection


_REGISTER_URL = "/auth/register"
_JIRA_AUTH_URL = "/jira/auth/url"
_JIRA_CALLBACK = "/jira/auth/callback"
_JIRA_STATUS = "/jira/status"
_JIRA_PROJECTS = "/jira/projects"
_JIRA_TICKETS = "/jira/tickets"
_JIRA_DISCONNECT = "/jira/connection"


async def _create_user_headers(async_client, email=None):
    email = email or f"jira-{uuid.uuid4().hex[:6]}@test.com"
    resp = await async_client.post(_REGISTER_URL, json={
        "email": email, "password": "Str0ngP@ss!", "full_name": "Jira User",
    })
    user_id = resp.json()["user"]["id"]
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


async def _add_jira_connection(db_session, user_id, test_settings):
    fernet = Fernet(test_settings.JIRA_ENCRYPTION_KEY.encode())
    conn = JiraConnection(
        user_id=uuid.UUID(user_id),
        cloud_id="cloud-test",
        site_url="https://test.atlassian.net",
        access_token_enc=fernet.encrypt(b"at"),
        refresh_token_enc=fernet.encrypt(b"rt"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(conn)
    await db_session.commit()
    return conn


# ── GET /jira/auth/url ────────────────────────────────────────────────────


class TestGetAuthUrl:
    async def test_get_auth_url_200(self, async_client, test_settings):
        headers, _ = await _create_user_headers(async_client)
        with patch("app.jira.service.settings", test_settings):
            resp = await async_client.get(_JIRA_AUTH_URL, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "authorization_url" in body
        assert "state" in body

    async def test_get_auth_url_requires_auth(self, async_client):
        resp = await async_client.get(_JIRA_AUTH_URL)
        assert resp.status_code == 401


# ── GET /jira/auth/callback ───────────────────────────────────────────────


class TestAuthCallback:
    async def test_callback_success_redirects_with_status_success(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)

        from app.jira.service import JiraService
        with patch("app.jira.service.settings", test_settings):
            _, state = JiraService.generate_auth_url(user_id)

        with patch("app.jira.service.JiraService.handle_callback", new_callable=AsyncMock, return_value=None):
            resp = await async_client.get(
                _JIRA_CALLBACK,
                params={"code": "auth-code", "state": state},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "status=success" in resp.headers.get("location", "")

    async def test_callback_invalid_state_redirects_with_error(self, async_client, test_settings):
        from app.jira.service import JiraOAuthError
        with patch("app.jira.service.JiraService.handle_callback", new_callable=AsyncMock, side_effect=JiraOAuthError("bad state")):
            resp = await async_client.get(
                _JIRA_CALLBACK,
                params={"code": "x", "state": "tampered"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "status=error" in resp.headers.get("location", "")

    async def test_callback_no_auth_required(self, async_client):
        from app.jira.service import JiraOAuthError
        with patch("app.jira.service.JiraService.handle_callback", new_callable=AsyncMock, side_effect=JiraOAuthError("no user")):
            resp = await async_client.get(
                _JIRA_CALLBACK,
                params={"code": "x", "state": "y"},
                follow_redirects=False,
            )
        # Should NOT return 401 — callback does not require Bearer auth
        assert resp.status_code != 401


# ── GET /jira/status ──────────────────────────────────────────────────────


class TestJiraStatus:
    async def test_status_connected_200(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        resp = await async_client.get(_JIRA_STATUS, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["connected"] is True
        assert body["cloud_id"] == "cloud-test"
        assert body["jira_site_url"] == "https://test.atlassian.net"

    async def test_status_not_connected_200(self, async_client):
        headers, _ = await _create_user_headers(async_client)
        resp = await async_client.get(_JIRA_STATUS, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["connected"] is False


# ── GET /jira/projects ────────────────────────────────────────────────────


class TestJiraProjects:
    async def test_projects_200_returns_list(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        mock_projects = [
            {"id": "1", "key": "PROJ", "name": "Project A"},
            {"id": "2", "key": "SEC", "name": "Security"},
        ]
        with patch("app.jira.service.JiraService._make_jira_request", new_callable=AsyncMock, return_value=mock_projects):
            resp = await async_client.get(_JIRA_PROJECTS, headers=headers)

        assert resp.status_code == 200
        projects = resp.json()["projects"]
        assert len(projects) == 2
        assert projects[0]["key"] == "PROJ"

    async def test_projects_403_no_jira_connection(self, async_client):
        headers, _ = await _create_user_headers(async_client)
        resp = await async_client.get(_JIRA_PROJECTS, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["code"] == "JIRA_NOT_CONNECTED"


# ── GET /jira/projects/{project_key}/issue-types ──────────────────────────


class TestIssueTypes:
    async def test_issue_types_200(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        mock_project_data = {
            "issueTypes": [
                {"id": "1", "name": "Bug", "untranslatedName": "Bug"},
                {"id": "2", "name": "Task", "untranslatedName": "Task"},
            ]
        }
        with patch("app.jira.service.JiraService._make_jira_request", new_callable=AsyncMock, return_value=mock_project_data):
            resp = await async_client.get(f"{_JIRA_PROJECTS}/SEC/issue-types", headers=headers)

        assert resp.status_code == 200
        issue_types = resp.json()["issue_types"]
        assert len(issue_types) == 2
        task_type = next(it for it in issue_types if it["name"] == "Task")
        assert task_type["is_default"] is True


# ── POST /jira/tickets ────────────────────────────────────────────────────


class TestCreateTicket:
    async def test_create_ticket_201(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.schemas import TicketCreatedBy, TicketResponse
        mock_resp = TicketResponse(
            id=uuid.uuid4(),
            jira_ticket_key="SEC-42",
            jira_ticket_url="https://test.atlassian.net/browse/SEC-42",
            summary="Test finding",
            issue_type="Task",
            source="ui",
            created_at=datetime.now(timezone.utc),
            created_by=TicketCreatedBy(id=uuid.UUID(user_id), full_name="Jira User"),
        )
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_resp):
            resp = await async_client.post(
                _JIRA_TICKETS,
                json={"project_key": "SEC", "summary": "Test finding"},
                headers=headers,
            )
        assert resp.status_code == 201
        body = resp.json()
        assert "jira_ticket_key" in body
        assert "created_by" in body

    async def test_create_ticket_source_is_ui(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.schemas import TicketCreatedBy, TicketResponse
        mock_resp = TicketResponse(
            id=uuid.uuid4(), jira_ticket_key="SEC-1",
            jira_ticket_url="https://x/SEC-1", summary="s",
            issue_type="Task", source="ui",
            created_at=datetime.now(timezone.utc),
            created_by=TicketCreatedBy(id=uuid.UUID(user_id), full_name="U"),
        )
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_resp) as mock_create:
            await async_client.post(
                _JIRA_TICKETS,
                json={"project_key": "SEC", "summary": "s"},
                headers=headers,
            )
            assert mock_create.call_args[0][2] == "ui"

    async def test_create_ticket_403_no_jira(self, async_client):
        headers, _ = await _create_user_headers(async_client)
        from app.jira.service import JiraNotConnectedError
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, side_effect=JiraNotConnectedError()):
            resp = await async_client.post(
                _JIRA_TICKETS,
                json={"project_key": "SEC", "summary": "s"},
                headers=headers,
            )
        assert resp.status_code == 403
        assert resp.json()["code"] == "JIRA_NOT_CONNECTED"

    async def test_create_ticket_400_invalid_project(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.service import JiraAPIError
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, side_effect=JiraAPIError("404 not found")):
            resp = await async_client.post(
                _JIRA_TICKETS,
                json={"project_key": "NOPE", "summary": "s"},
                headers=headers,
            )
        assert resp.status_code == 400
        assert resp.json()["code"] == "JIRA_PROJECT_NOT_FOUND"

    async def test_create_ticket_502_jira_api_error(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.service import JiraAPIError
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, side_effect=JiraAPIError("500 internal error")):
            resp = await async_client.post(
                _JIRA_TICKETS,
                json={"project_key": "SEC", "summary": "s"},
                headers=headers,
            )
        assert resp.status_code == 502
        assert resp.json()["code"] == "JIRA_API_ERROR"

    async def test_create_ticket_422_summary_too_long(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        resp = await async_client.post(
            _JIRA_TICKETS,
            json={"project_key": "SEC", "summary": "x" * 256},
            headers=headers,
        )
        assert resp.status_code == 422


# ── GET /jira/tickets ─────────────────────────────────────────────────────


class TestGetTickets:
    async def _create_tickets(self, async_client, headers, count, project="SEC"):
        from app.jira.schemas import TicketCreatedBy, TicketResponse
        results = []
        for i in range(count):
            mock_resp = TicketResponse(
                id=uuid.uuid4(),
                jira_ticket_key=f"{project}-{i}",
                jira_ticket_url=f"https://x/{project}-{i}",
                summary=f"Ticket {i}",
                issue_type="Task",
                source="ui",
                created_at=datetime.now(timezone.utc),
                created_by=TicketCreatedBy(id=uuid.uuid4(), full_name="U"),
            )
            with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_resp):
                await async_client.post(
                    _JIRA_TICKETS,
                    json={"project_key": project, "summary": f"Ticket {i}"},
                    headers=headers,
                )

    async def test_get_tickets_200(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.schemas import TicketCreatedBy, TicketResponse
        mock_list = [
            TicketResponse(
                id=uuid.uuid4(), jira_ticket_key=f"SEC-{i}",
                jira_ticket_url=f"https://x/SEC-{i}", summary=f"T{i}",
                issue_type="Task", source="ui",
                created_at=datetime.now(timezone.utc),
                created_by=TicketCreatedBy(id=uuid.UUID(user_id), full_name="U"),
            ) for i in range(3)
        ]
        with patch("app.jira.service.JiraService.get_recent_tickets", new_callable=AsyncMock, return_value=mock_list):
            resp = await async_client.get(
                _JIRA_TICKETS,
                params={"project_key": "SEC"},
                headers=headers,
            )
        assert resp.status_code == 200
        assert len(resp.json()["tickets"]) == 3

    async def test_get_tickets_filters_by_project_key(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        from app.jira.schemas import TicketCreatedBy, TicketResponse
        mock_tickets = [
            TicketResponse(
                id=uuid.uuid4(), jira_ticket_key="ALPHA-1",
                jira_ticket_url="https://x/ALPHA-1", summary="A",
                issue_type="Task", source="ui",
                created_at=datetime.now(timezone.utc),
                created_by=TicketCreatedBy(id=uuid.UUID(user_id), full_name="U"),
            )
        ]
        with patch("app.jira.service.JiraService.get_recent_tickets", new_callable=AsyncMock, return_value=mock_tickets) as mock_get:
            resp = await async_client.get(
                _JIRA_TICKETS,
                params={"project_key": "ALPHA"},
                headers=headers,
            )
            assert mock_get.call_args[0][0] == "ALPHA"

    async def test_get_tickets_default_limit_10(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        with patch("app.jira.service.JiraService.get_recent_tickets", new_callable=AsyncMock, return_value=[]) as mock_get:
            await async_client.get(
                _JIRA_TICKETS,
                params={"project_key": "SEC"},
                headers=headers,
            )
            assert mock_get.call_args[0][1] == 10

    async def test_get_tickets_custom_limit(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        with patch("app.jira.service.JiraService.get_recent_tickets", new_callable=AsyncMock, return_value=[]) as mock_get:
            await async_client.get(
                _JIRA_TICKETS,
                params={"project_key": "SEC", "limit": 5},
                headers=headers,
            )
            assert mock_get.call_args[0][1] == 5


# ── DELETE /jira/connection ───────────────────────────────────────────────


class TestDisconnect:
    async def test_disconnect_200(self, async_client, db_session, test_settings):
        headers, user_id = await _create_user_headers(async_client)
        await _add_jira_connection(db_session, user_id, test_settings)

        resp = await async_client.delete(_JIRA_DISCONNECT, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Jira connection removed"

    async def test_disconnect_requires_auth(self, async_client):
        resp = await async_client.delete(_JIRA_DISCONNECT)
        assert resp.status_code == 401
