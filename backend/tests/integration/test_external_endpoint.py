"""Integration tests for POST /api/v1/tickets (external ticket creation).

Tests per docs/backend_hld.md § 5.3 (External API Key Auth), § 6.5, § 7 (Rate Limiting).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet

from app.api_keys.service import ApiKeyService
from app.models.jira_connection import JiraConnection


_REGISTER_URL = "/auth/register"
_API_KEYS_URL = "/api-keys"
_EXTERNAL_TICKETS_URL = "/api/v1/tickets"


async def _setup_user_with_key_and_jira(async_client, db_session, test_settings):
    """Create a user, API key, and mock Jira connection. Return (raw_api_key, user_id)."""
    reg_resp = await async_client.post(_REGISTER_URL, json={
        "email": f"ext-{uuid.uuid4().hex[:6]}@test.com",
        "password": "Str0ngP@ss!",
        "full_name": "External User",
    })
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]

    key_resp = await async_client.post(
        _API_KEYS_URL,
        json={"name": "ext-key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    raw_key = key_resp.json()["key"]

    fernet = Fernet(test_settings.JIRA_ENCRYPTION_KEY.encode())
    conn = JiraConnection(
        user_id=uuid.UUID(user_id),
        cloud_id="cloud-ext",
        site_url="https://ext.atlassian.net",
        access_token_enc=fernet.encrypt(b"at"),
        refresh_token_enc=fernet.encrypt(b"rt"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(conn)
    await db_session.commit()

    return raw_key, user_id


def _ticket_payload(project_key="SEC", summary="Test finding"):
    return {"project_key": project_key, "summary": summary}


def _mock_jira_create_response():
    """Patch JiraService.create_ticket to return a mock TicketResponse."""
    from app.jira.schemas import TicketCreatedBy, TicketResponse
    return TicketResponse(
        id=uuid.uuid4(),
        jira_ticket_key="SEC-99",
        jira_ticket_url="https://ext.atlassian.net/browse/SEC-99",
        summary="Test finding",
        issue_type="Task",
        source="api",
        created_at=datetime.now(timezone.utc),
        created_by=TicketCreatedBy(id=uuid.uuid4(), full_name="External User"),
    )


# ── Happy Path ─────────────────────────────────────────────────────────────


class TestExternalHappyPath:
    async def test_create_ticket_via_api_key_201(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        mock_result = _mock_jira_create_response()
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_result):
            resp = await async_client.post(
                _EXTERNAL_TICKETS_URL,
                json=_ticket_payload(),
                headers={"X-API-Key": raw_key},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert "jira_ticket_key" in body
        assert "jira_ticket_url" in body
        assert "summary" in body
        assert "created_at" in body

    async def test_ticket_source_is_api(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        mock_result = _mock_jira_create_response()
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_result) as mock_create:
            await async_client.post(
                _EXTERNAL_TICKETS_URL,
                json=_ticket_payload(),
                headers={"X-API-Key": raw_key},
            )
            call_args = mock_create.call_args
            assert call_args[0][2] == "api"  # source argument

    async def test_ticket_created_under_key_owner_jira_identity(self, async_client, db_session, test_settings):
        raw_key, user_id = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        mock_result = _mock_jira_create_response()
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_result) as mock_create:
            await async_client.post(
                _EXTERNAL_TICKETS_URL,
                json=_ticket_payload(),
                headers={"X-API-Key": raw_key},
            )
            call_args = mock_create.call_args
            assert call_args[0][0] == user_id  # user_id argument


# ── Error Paths ────────────────────────────────────────────────────────────


class TestExternalErrors:
    async def test_missing_api_key_401_INVALID_API_KEY(self, async_client):
        resp = await async_client.post(_EXTERNAL_TICKETS_URL, json=_ticket_payload())
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_API_KEY"

    async def test_invalid_api_key_401_INVALID_API_KEY(self, async_client):
        resp = await async_client.post(
            _EXTERNAL_TICKETS_URL,
            json=_ticket_payload(),
            headers={"X-API-Key": "random-invalid-key"},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_API_KEY"

    async def test_revoked_api_key_401_API_KEY_REVOKED(self, async_client, db_session, test_settings):
        raw_key, user_id = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        from sqlalchemy import select
        from app.models.api_key import ApiKey
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        result = await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        api_key = result.scalar_one()
        api_key.is_active = False
        await db_session.commit()

        resp = await async_client.post(
            _EXTERNAL_TICKETS_URL,
            json=_ticket_payload(),
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == "API_KEY_REVOKED"

    async def test_key_owner_no_jira_connection_403_JIRA_NOT_CONNECTED(self, async_client, db_session, test_settings):
        reg_resp = await async_client.post(_REGISTER_URL, json={
            "email": f"nojira-{uuid.uuid4().hex[:6]}@test.com",
            "password": "Str0ngP@ss!",
            "full_name": "No Jira User",
        })
        token = reg_resp.json()["access_token"]
        key_resp = await async_client.post(
            _API_KEYS_URL,
            json={"name": "nojira-key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        raw_key = key_resp.json()["key"]

        from app.jira.service import JiraNotConnectedError
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, side_effect=JiraNotConnectedError("Jira not connected")):
            resp = await async_client.post(
                _EXTERNAL_TICKETS_URL,
                json=_ticket_payload(),
                headers={"X-API-Key": raw_key},
            )
        assert resp.status_code == 403
        assert resp.json()["code"] == "JIRA_NOT_CONNECTED"

    async def test_validation_error_422(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)
        resp = await async_client.post(
            _EXTERNAL_TICKETS_URL,
            json={"summary": "Missing project_key"},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    async def test_summary_too_long_422(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)
        resp = await async_client.post(
            _EXTERNAL_TICKETS_URL,
            json={"project_key": "SEC", "summary": "x" * 256},
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 422

    async def test_jira_api_failure_502_JIRA_API_ERROR(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        from app.jira.service import JiraAPIError
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, side_effect=JiraAPIError("500 Internal")):
            resp = await async_client.post(
                _EXTERNAL_TICKETS_URL,
                json=_ticket_payload(),
                headers={"X-API-Key": raw_key},
            )
        assert resp.status_code == 502
        assert resp.json()["code"] == "JIRA_API_ERROR"


# ── Rate Limiting ──────────────────────────────────────────────────────────


class TestExternalRateLimit:
    async def test_rate_limit_429_RATE_LIMITED(self, async_client, db_session, test_settings):
        raw_key, _ = await _setup_user_with_key_and_jira(async_client, db_session, test_settings)

        mock_result = _mock_jira_create_response()
        with patch("app.jira.service.JiraService.create_ticket", new_callable=AsyncMock, return_value=mock_result):
            last_status = 201
            for i in range(21):
                resp = await async_client.post(
                    _EXTERNAL_TICKETS_URL,
                    json=_ticket_payload(summary=f"Rate test {i}"),
                    headers={"X-API-Key": raw_key},
                )
                last_status = resp.status_code
                if last_status == 429:
                    break

        assert last_status == 429
        body = resp.json()
        assert body["code"] == "RATE_LIMITED"
        assert "Rate limit exceeded" in body["detail"]
