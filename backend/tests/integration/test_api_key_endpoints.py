"""Integration tests for API key CRUD endpoints.

Tests per docs/backend_hld.md § 6.4 and docs/db_hld.md § 3.3 (soft-delete).
"""

import uuid

import pytest

from app.api_keys.service import ApiKeyService


_REGISTER_URL = "/auth/register"
_API_KEYS_URL = "/api-keys"


async def _create_user_and_get_headers(async_client, email=None):
    email = email or f"test-{uuid.uuid4().hex[:8]}@example.com"
    resp = await async_client.post(_REGISTER_URL, json={
        "email": email,
        "password": "Str0ngP@ss!",
        "full_name": "Test User",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── POST /api-keys ────────────────────────────────────────────────────────


class TestCreateApiKey:
    async def test_create_api_key_201_returns_raw_key(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        resp = await async_client.post(_API_KEYS_URL, json={"name": "CI Key"}, headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert "id" in body
        assert body["name"] == "CI Key"
        assert body["key"].startswith("ihub_live_")
        assert "created_at" in body

    async def test_create_api_key_requires_auth(self, async_client):
        resp = await async_client.post(_API_KEYS_URL, json={"name": "No Auth"})
        assert resp.status_code == 401

    async def test_create_api_key_422_empty_name(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        resp = await async_client.post(_API_KEYS_URL, json={"name": ""}, headers=headers)
        assert resp.status_code == 422

    async def test_create_api_key_422_name_too_long(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        resp = await async_client.post(_API_KEYS_URL, json={"name": "x" * 101}, headers=headers)
        assert resp.status_code == 422


# ── GET /api-keys ──────────────────────────────────────────────────────────


class TestListApiKeys:
    async def test_list_api_keys_200_returns_masked_keys(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        await async_client.post(_API_KEYS_URL, json={"name": "Key 1"}, headers=headers)
        await async_client.post(_API_KEYS_URL, json={"name": "Key 2"}, headers=headers)

        resp = await async_client.get(_API_KEYS_URL, headers=headers)
        assert resp.status_code == 200
        keys = resp.json()["api_keys"]
        assert len(keys) == 2
        for k in keys:
            assert "key_prefix" in k
            assert "key" not in k  # raw key not exposed in listing

    async def test_list_api_keys_excludes_revoked(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        r1 = await async_client.post(_API_KEYS_URL, json={"name": "Active"}, headers=headers)
        r2 = await async_client.post(_API_KEYS_URL, json={"name": "Revoked"}, headers=headers)
        revoke_id = r2.json()["id"]

        await async_client.delete(f"{_API_KEYS_URL}/{revoke_id}", headers=headers)

        resp = await async_client.get(_API_KEYS_URL, headers=headers)
        keys = resp.json()["api_keys"]
        assert len(keys) == 1
        assert keys[0]["name"] == "Active"

    async def test_list_api_keys_requires_auth(self, async_client):
        resp = await async_client.get(_API_KEYS_URL)
        assert resp.status_code == 401

    async def test_list_api_keys_only_own_keys(self, async_client):
        headers_a = await _create_user_and_get_headers(async_client, email="a@keys.com")
        headers_b = await _create_user_and_get_headers(async_client, email="b@keys.com")

        await async_client.post(_API_KEYS_URL, json={"name": "A Key"}, headers=headers_a)
        await async_client.post(_API_KEYS_URL, json={"name": "B Key"}, headers=headers_b)

        resp_a = await async_client.get(_API_KEYS_URL, headers=headers_a)
        resp_b = await async_client.get(_API_KEYS_URL, headers=headers_b)

        assert len(resp_a.json()["api_keys"]) == 1
        assert resp_a.json()["api_keys"][0]["name"] == "A Key"
        assert len(resp_b.json()["api_keys"]) == 1
        assert resp_b.json()["api_keys"][0]["name"] == "B Key"


# ── DELETE /api-keys/{key_id} ─────────────────────────────────────────────


class TestRevokeApiKey:
    async def test_revoke_api_key_200(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        create_resp = await async_client.post(_API_KEYS_URL, json={"name": "ToRevoke"}, headers=headers)
        key_id = create_resp.json()["id"]

        resp = await async_client.delete(f"{_API_KEYS_URL}/{key_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["detail"] == "API key revoked"

    async def test_revoke_api_key_is_soft_delete(self, async_client, db_session):
        headers = await _create_user_and_get_headers(async_client)
        create_resp = await async_client.post(_API_KEYS_URL, json={"name": "SoftDel"}, headers=headers)
        key_id = create_resp.json()["id"]

        await async_client.delete(f"{_API_KEYS_URL}/{key_id}", headers=headers)

        from sqlalchemy import select
        from app.models.api_key import ApiKey
        result = await db_session.execute(select(ApiKey).where(ApiKey.id == uuid.UUID(key_id)))
        key = result.scalar_one()
        assert key.is_active is False

    async def test_revoke_other_users_key_404(self, async_client):
        headers_a = await _create_user_and_get_headers(async_client, email="revoke-a@test.com")
        headers_b = await _create_user_and_get_headers(async_client, email="revoke-b@test.com")

        create_resp = await async_client.post(_API_KEYS_URL, json={"name": "A's Key"}, headers=headers_a)
        key_id = create_resp.json()["id"]

        resp = await async_client.delete(f"{_API_KEYS_URL}/{key_id}", headers=headers_b)
        assert resp.status_code == 404

    async def test_revoke_nonexistent_key_404(self, async_client):
        headers = await _create_user_and_get_headers(async_client)
        fake_id = str(uuid.uuid4())
        resp = await async_client.delete(f"{_API_KEYS_URL}/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_revoke_requires_auth(self, async_client):
        resp = await async_client.delete(f"{_API_KEYS_URL}/{uuid.uuid4()}")
        assert resp.status_code == 401
