"""Unit tests for app/auth/utils.py — password hashing and JWT management.

Tests per docs/backend_hld.md § 5.1 (Token Strategy) and
docs/db_hld.md § 5.3 (Passwords — Bcrypt).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from jose import jwt

from app.auth.utils import (
    InvalidTokenError,
    TokenExpiredError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

_TEST_SECRET = "test-secret-key-0123456789abcdef0123456789abcdef"
_TEST_SETTINGS_PATCH = {
    "SECRET_KEY": _TEST_SECRET,
    "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7,
}


def _make_settings(**overrides):
    from app.config import Settings

    defaults = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "JIRA_ENCRYPTION_KEY": "dGVzdC1lbmNyeXB0aW9uLWtleS0xMjM0NTY3OA==",
        **_TEST_SETTINGS_PATCH,
        **overrides,
    }
    return Settings(**defaults)


_settings = _make_settings()


# ── Password Hashing (bcrypt, 12 rounds) ──────────────────────────────────


class TestHashPassword:
    @patch("app.auth.utils.settings", _settings)
    def test_hash_password_returns_bcrypt_hash(self):
        hashed = hash_password("MySecureP@ss1")
        assert hashed.startswith("$2b$")

    @patch("app.auth.utils.settings", _settings)
    def test_hash_password_uses_12_rounds(self):
        hashed = hash_password("MySecureP@ss1")
        assert hashed.startswith("$2b$12$")

    @patch("app.auth.utils.settings", _settings)
    def test_verify_password_correct(self):
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    @patch("app.auth.utils.settings", _settings)
    def test_verify_password_incorrect(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    @patch("app.auth.utils.settings", _settings)
    def test_hash_password_unique_salts(self):
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2


# ── JWT Access Token ──────────────────────────────────────────────────────


class TestAccessToken:
    @patch("app.auth.utils.settings", _settings)
    def test_create_access_token_contains_correct_claims(self):
        token = create_access_token("user-123", "u@example.com")
        payload = jwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "user-123"
        assert payload["email"] == "u@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload

    @patch("app.auth.utils.settings", _settings)
    def test_access_token_expires_in_15_minutes(self):
        before = datetime.now(timezone.utc)
        token = create_access_token("user-123", "u@example.com")
        after = datetime.now(timezone.utc)

        payload = jwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected = before + timedelta(minutes=15)

        assert abs((exp - expected).total_seconds()) < 5

    @patch("app.auth.utils.settings", _settings)
    def test_decode_valid_access_token(self):
        token = create_access_token("user-456", "test@test.com")
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert payload["email"] == "test@test.com"
        assert payload["type"] == "access"

    @patch("app.auth.utils.settings", _settings)
    def test_decode_expired_token_raises(self):
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {"sub": "user-1", "email": "a@b.c", "exp": expire, "type": "access"}
        token = jwt.encode(payload, _TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenExpiredError):
            decode_token(token)

    @patch("app.auth.utils.settings", _settings)
    def test_decode_invalid_token_raises(self):
        with pytest.raises(InvalidTokenError):
            decode_token("not.a.valid.jwt.string")

    @patch("app.auth.utils.settings", _settings)
    def test_decode_token_wrong_secret_raises(self):
        token = jwt.encode(
            {"sub": "u1", "email": "e@e.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "type": "access"},
            "different-secret-key",
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_token(token)


# ── JWT Refresh Token ─────────────────────────────────────────────────────


class TestRefreshToken:
    @patch("app.auth.utils.settings", _settings)
    def test_create_refresh_token_contains_correct_claims(self):
        token = create_refresh_token("user-789")
        payload = jwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "user-789"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    @patch("app.auth.utils.settings", _settings)
    def test_refresh_token_expires_in_7_days(self):
        before = datetime.now(timezone.utc)
        token = create_refresh_token("user-789")
        payload = jwt.decode(token, _TEST_SECRET, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected = before + timedelta(days=7)
        assert abs((exp - expected).total_seconds()) < 5

    @patch("app.auth.utils.settings", _settings)
    def test_access_and_refresh_tokens_have_different_type_claims(self):
        access = create_access_token("u1", "e@e.com")
        refresh = create_refresh_token("u1")

        access_payload = jwt.decode(access, _TEST_SECRET, algorithms=["HS256"])
        refresh_payload = jwt.decode(refresh, _TEST_SECRET, algorithms=["HS256"])

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["type"] != refresh_payload["type"]
