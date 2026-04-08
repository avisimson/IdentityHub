"""Integration tests for all 6 auth API endpoints.

Tests per docs/backend_hld.md § 6.2 — request/response contracts and error codes.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt as jose_jwt


_REGISTER_URL = "/auth/register"
_LOGIN_URL = "/auth/login"
_REFRESH_URL = "/auth/refresh"
_ME_URL = "/auth/me"
_LOGOUT_URL = "/auth/logout"
_GOOGLE_URL = "/auth/google"


def _register_payload(email="test@example.com", password="Str0ngP@ss!", full_name="Test User"):
    return {"email": email, "password": password, "full_name": full_name}


# ── POST /auth/register ───────────────────────────────────────────────────


class TestRegisterEndpoint:
    async def test_register_201_returns_token_and_user(self, async_client):
        resp = await async_client.post(_REGISTER_URL, json=_register_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        user = body["user"]
        assert "id" in user
        assert user["email"] == "test@example.com"
        assert user["full_name"] == "Test User"
        assert user["auth_provider"] == "local"

    async def test_register_sets_refresh_token_cookie(self, async_client):
        resp = await async_client.post(_REGISTER_URL, json=_register_payload())
        cookies = resp.headers.get_list("set-cookie")
        cookie_str = "; ".join(cookies).lower()
        assert "refresh_token=" in cookie_str
        assert "httponly" in cookie_str
        assert "samesite=lax" in cookie_str
        assert "path=/auth" in cookie_str

    async def test_register_409_duplicate_email(self, async_client):
        payload = _register_payload(email="dupe@example.com")
        await async_client.post(_REGISTER_URL, json=payload)
        resp = await async_client.post(_REGISTER_URL, json=payload)
        assert resp.status_code == 409
        body = resp.json()
        assert body["code"] == "EMAIL_EXISTS"
        assert "Email already registered" in body["detail"]

    async def test_register_422_invalid_email(self, async_client):
        resp = await async_client.post(_REGISTER_URL, json=_register_payload(email="notanemail"))
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    async def test_register_422_short_password(self, async_client):
        resp = await async_client.post(_REGISTER_URL, json=_register_payload(password="short"))
        assert resp.status_code == 422

    async def test_register_422_missing_full_name(self, async_client):
        resp = await async_client.post(_REGISTER_URL, json={"email": "a@b.com", "password": "LongEnough1!"})
        assert resp.status_code == 422


# ── POST /auth/login ──────────────────────────────────────────────────────


class TestLoginEndpoint:
    async def test_login_200_valid_credentials(self, async_client):
        await async_client.post(_REGISTER_URL, json=_register_payload(email="login@example.com"))
        resp = await async_client.post(_LOGIN_URL, json={"email": "login@example.com", "password": "Str0ngP@ss!"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["email"] == "login@example.com"

    async def test_login_401_wrong_password(self, async_client):
        await async_client.post(_REGISTER_URL, json=_register_payload(email="wrongpw@example.com"))
        resp = await async_client.post(_LOGIN_URL, json={"email": "wrongpw@example.com", "password": "WrongPass1!"})
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "INVALID_CREDENTIALS"
        assert "Invalid email or password" in body["detail"]

    async def test_login_401_nonexistent_email(self, async_client):
        resp = await async_client.post(_LOGIN_URL, json={"email": "nobody@example.com", "password": "pass"})
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_CREDENTIALS"


# ── POST /auth/refresh ────────────────────────────────────────────────────


class TestRefreshEndpoint:
    async def test_refresh_200_with_valid_cookie(self, async_client):
        reg_resp = await async_client.post(_REGISTER_URL, json=_register_payload(email="refresh@example.com"))
        assert reg_resp.status_code == 201

        resp = await async_client.post(_REFRESH_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "user" in body

    async def test_refresh_401_no_cookie(self, async_client):
        async_client.cookies.clear()
        resp = await async_client.post(_REFRESH_URL)
        assert resp.status_code == 401
        assert resp.json()["code"] == "INVALID_REFRESH_TOKEN"

    async def test_refresh_401_invalid_cookie(self, async_client):
        async_client.cookies.set("refresh_token", "garbage-token-value", domain="testserver", path="/auth")
        resp = await async_client.post(_REFRESH_URL)
        assert resp.status_code == 401


# ── GET /auth/me ───────────────────────────────────────────────────────────


class TestMeEndpoint:
    async def test_me_200_with_valid_token(self, async_client):
        reg_resp = await async_client.post(_REGISTER_URL, json=_register_payload(email="me@example.com"))
        token = reg_resp.json()["access_token"]
        resp = await async_client.get(_ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    async def test_me_401_no_token(self, async_client):
        resp = await async_client.get(_ME_URL)
        assert resp.status_code == 401
        assert resp.json()["code"] == "NOT_AUTHENTICATED"

    async def test_me_401_expired_token(self, async_client, test_settings):
        from datetime import datetime, timedelta, timezone
        expired_payload = {
            "sub": "fake-user-id",
            "email": "exp@test.com",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        }
        expired_token = jose_jwt.encode(expired_payload, test_settings.SECRET_KEY, algorithm="HS256")
        resp = await async_client.get(_ME_URL, headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401


# ── POST /auth/logout ─────────────────────────────────────────────────────


class TestLogoutEndpoint:
    async def test_logout_200_clears_cookie(self, async_client):
        await async_client.post(_REGISTER_URL, json=_register_payload(email="logout@example.com"))
        resp = await async_client.post(_LOGOUT_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["detail"] == "Logged out successfully"


# ── POST /auth/google ─────────────────────────────────────────────────────


class TestGoogleEndpoint:
    def _mock_google_response(self, email="google@test.com", sub="g-sub-1"):
        id_token = jose_jwt.encode(
            {"sub": sub, "email": email, "name": "Google User"},
            "fake-key",
            algorithm="HS256",
        )
        return MagicMock(
            status_code=200,
            json=lambda: {"access_token": "gat", "id_token": id_token},
        )

    async def test_google_auth_200_new_user(self, async_client, test_settings):
        mock_resp = self._mock_google_response()
        with patch("app.auth.service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            resp = await async_client.post(_GOOGLE_URL, json={"code": "gcode", "redirect_uri": "http://localhost"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["auth_provider"] == "google"

    async def test_google_auth_200_existing_user_links_account(self, async_client, test_settings):
        await async_client.post(_REGISTER_URL, json=_register_payload(email="link@test.com"))

        mock_resp = self._mock_google_response(email="link@test.com", sub="link-sub")
        with patch("app.auth.service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            resp = await async_client.post(_GOOGLE_URL, json={"code": "linkcode", "redirect_uri": "http://localhost"})

        assert resp.status_code == 200
        user = resp.json()["user"]
        assert user["email"] == "link@test.com"
