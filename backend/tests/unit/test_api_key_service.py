"""Unit tests for app/api_keys/service.py — API key generation, validation, revocation.

Tests per docs/db_hld.md § 3.3, § 5.2 and docs/backend_hld.md § 6.4, § 6.5.
"""

import hashlib

import pytest
from fastapi import HTTPException

from app.api_keys.service import ApiKeyService


# ── Key Generation ─────────────────────────────────────────────────────────


class TestGenerateKey:
    async def test_generate_key_format(self, db_session, test_user):
        user = await test_user()
        _key_row, raw_key = await ApiKeyService.generate_key(user.id, "test", db_session)
        assert raw_key.startswith("ihub_live_")
        hex_part = raw_key.removeprefix("ihub_live_")
        assert len(hex_part) == 48
        int(hex_part, 16)  # must be valid hex

    async def test_generate_key_prefix_is_first_12_chars(self, db_session, test_user):
        user = await test_user()
        key_row, raw_key = await ApiKeyService.generate_key(user.id, "test", db_session)
        assert key_row.key_prefix == raw_key[:12]

    async def test_generate_key_hash_is_sha256(self, db_session, test_user):
        user = await test_user()
        key_row, raw_key = await ApiKeyService.generate_key(user.id, "test", db_session)
        expected = hashlib.sha256(raw_key.encode()).hexdigest()
        assert key_row.key_hash == expected

    async def test_generate_key_unique_each_call(self, db_session, test_user):
        user = await test_user()
        _, key1 = await ApiKeyService.generate_key(user.id, "k1", db_session)
        _, key2 = await ApiKeyService.generate_key(user.id, "k2", db_session)
        assert key1 != key2

    async def test_generate_key_stored_in_db(self, db_session, test_user):
        user = await test_user()
        key_row, _ = await ApiKeyService.generate_key(user.id, "stored", db_session)
        assert key_row.is_active is True
        assert key_row.id is not None


# ── Key Validation ─────────────────────────────────────────────────────────


class TestValidateKey:
    async def test_validate_valid_key_returns_key_and_user(self, db_session, test_user):
        user = await test_user()
        _, raw_key = await ApiKeyService.generate_key(user.id, "valid", db_session)
        api_key, returned_user = await ApiKeyService.validate_api_key(raw_key, db_session)
        assert api_key.user_id == user.id
        assert returned_user.id == user.id

    async def test_validate_key_updates_last_used_at(self, db_session, test_user):
        user = await test_user()
        key_row, raw_key = await ApiKeyService.generate_key(user.id, "usage", db_session)
        assert key_row.last_used_at is None
        api_key, _ = await ApiKeyService.validate_api_key(raw_key, db_session)
        assert api_key.last_used_at is not None

    async def test_validate_invalid_key_raises_INVALID_API_KEY(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            await ApiKeyService.validate_api_key("random-garbage-key", db_session)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "INVALID_API_KEY"

    async def test_validate_revoked_key_raises_API_KEY_REVOKED(self, db_session, test_user):
        user = await test_user()
        key_row, raw_key = await ApiKeyService.generate_key(user.id, "revokeme", db_session)
        await ApiKeyService.revoke_key(user.id, key_row.id, db_session)
        with pytest.raises(HTTPException) as exc_info:
            await ApiKeyService.validate_api_key(raw_key, db_session)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "API_KEY_REVOKED"


# ── Key Revocation ─────────────────────────────────────────────────────────


class TestRevokeKey:
    async def test_revoke_key_sets_is_active_false(self, db_session, test_user):
        user = await test_user()
        key_row, _ = await ApiKeyService.generate_key(user.id, "torevoke", db_session)
        await ApiKeyService.revoke_key(user.id, key_row.id, db_session)
        await db_session.refresh(key_row)
        assert key_row.is_active is False

    async def test_revoke_key_not_owned_by_user_raises(self, db_session, test_user):
        user_a = await test_user(email="a@test.com")
        user_b = await test_user(email="b@test.com")
        key_row, _ = await ApiKeyService.generate_key(user_a.id, "a-key", db_session)
        with pytest.raises(HTTPException) as exc_info:
            await ApiKeyService.revoke_key(user_b.id, key_row.id, db_session)
        assert exc_info.value.status_code == 404


# ── Key Listing ────────────────────────────────────────────────────────────


class TestListKeys:
    async def test_list_keys_only_returns_active(self, db_session, test_user):
        user = await test_user()
        k1, _ = await ApiKeyService.generate_key(user.id, "active-key", db_session)
        k2, _ = await ApiKeyService.generate_key(user.id, "revoked-key", db_session)
        await ApiKeyService.revoke_key(user.id, k2.id, db_session)

        keys = await ApiKeyService.list_keys(user.id, db_session)
        assert len(keys) == 1
        assert keys[0].id == k1.id

    async def test_list_keys_returns_prefix_not_hash(self, db_session, test_user):
        user = await test_user()
        await ApiKeyService.generate_key(user.id, "prefix-test", db_session)
        keys = await ApiKeyService.list_keys(user.id, db_session)
        key = keys[0]
        assert key.key_prefix is not None
        assert len(key.key_prefix) == 12
