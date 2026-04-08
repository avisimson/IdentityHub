"""Unit tests for app/auth/service.py — AuthService and GoogleAuthService.

Tests per docs/backend_hld.md § 5.1 (Auth flows), § 6.2 (Error codes),
and docs/db_hld.md § 3.1 (User schema, account-linking design note).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt as jose_jwt

from app.auth.service import AuthService, GoogleAuthService
from app.auth.utils import decode_token


# ── AuthService.register ──────────────────────────────────────────────────


class TestRegister:
    async def test_register_creates_user_with_hashed_password(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            user, _, _ = await AuthService.register(
                db_session, "new@example.com", "Str0ngP@ss!", "New User"
            )
        assert user.email == "new@example.com"
        assert user.password_hash != "Str0ngP@ss!"
        assert user.auth_provider == "local"

    async def test_register_normalizes_email_to_lowercase(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            user, _, _ = await AuthService.register(
                db_session, "User@EXAMPLE.COM", "Str0ngP@ss!", "User"
            )
        assert user.email == "user@example.com"

    async def test_register_returns_access_and_refresh_tokens(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            _, access, refresh = await AuthService.register(
                db_session, "tokens@example.com", "Str0ngP@ss!", "Tokens"
            )
        assert access and len(access) > 10
        assert refresh and len(refresh) > 10

    async def test_register_duplicate_email_raises_409_EMAIL_EXISTS(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            await AuthService.register(
                db_session, "dupe@example.com", "Str0ngP@ss!", "First"
            )
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.register(
                    db_session, "dupe@example.com", "Str0ngP@ss!", "Second"
                )
        assert exc_info.value.status_code == 409
        assert exc_info.value.headers.get("X-Error-Code") == "EMAIL_EXISTS"


# ── AuthService.login ─────────────────────────────────────────────────────


class TestLogin:
    async def test_login_success_returns_tokens(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            await AuthService.register(
                db_session, "login@example.com", "Str0ngP@ss!", "Login User"
            )
            user, access, refresh = await AuthService.login(
                db_session, "login@example.com", "Str0ngP@ss!"
            )
        assert user.email == "login@example.com"
        assert access and refresh

    async def test_login_wrong_email_raises_401_INVALID_CREDENTIALS(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.login(db_session, "nobody@example.com", "pass")
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "INVALID_CREDENTIALS"

    async def test_login_wrong_password_raises_401_INVALID_CREDENTIALS(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            await AuthService.register(
                db_session, "wrongpw@example.com", "CorrectP@ss!", "User"
            )
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.login(db_session, "wrongpw@example.com", "WrongP@ss!")
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "INVALID_CREDENTIALS"

    async def test_login_google_only_user_no_password_raises_401(self, db_session, test_settings):
        from app.models.user import User as UserModel
        import uuid

        google_user = UserModel(
            id=uuid.uuid4(),
            email="google@example.com",
            password_hash=None,
            full_name="Google User",
            auth_provider="google",
        )
        db_session.add(google_user)
        await db_session.commit()

        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.login(db_session, "google@example.com", "any-password")
        assert exc_info.value.status_code == 401


# ── AuthService.refresh ───────────────────────────────────────────────────


class TestRefresh:
    async def test_refresh_valid_token_returns_new_tokens_and_user(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            user, _, refresh_token = await AuthService.register(
                db_session, "refresh@example.com", "Str0ngP@ss!", "Refresh"
            )
            returned_user, new_access, new_refresh = await AuthService.refresh(
                db_session, refresh_token
            )
        assert returned_user.id == user.id
        assert new_access and new_refresh

    async def test_refresh_expired_token_raises_401(self, db_session, test_settings):
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {"sub": "user-1", "exp": expire, "type": "refresh"}
        expired_token = jose_jwt.encode(payload, test_settings.SECRET_KEY, algorithm="HS256")

        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.refresh(db_session, expired_token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "INVALID_REFRESH_TOKEN"

    async def test_refresh_access_token_as_refresh_raises_401(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            _, access_token, _ = await AuthService.register(
                db_session, "accessasrefresh@example.com", "Str0ngP@ss!", "User"
            )
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.refresh(db_session, access_token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers.get("X-Error-Code") == "INVALID_REFRESH_TOKEN"


# ── GoogleAuthService ─────────────────────────────────────────────────────


def _mock_google_response(sub="google-123", email="guser@example.com", name="Google User"):
    """Build a mock httpx response for Google token exchange."""
    id_token = jose_jwt.encode(
        {"sub": sub, "email": email, "name": name},
        "fake-key",
        algorithm="HS256",
    )
    return MagicMock(
        status_code=200,
        json=lambda: {"access_token": "gat", "id_token": id_token},
    )


class TestGoogleAuth:
    async def test_google_auth_new_user_creates_account(self, db_session, test_settings):
        mock_resp = _mock_google_response()

        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings), \
             patch("app.auth.service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            instance = MockClient.return_value.__aenter__.return_value
            instance.post = AsyncMock(return_value=mock_resp)

            user, access, refresh = await GoogleAuthService.authenticate(
                db_session, "auth-code", "http://localhost/callback"
            )

        assert user.auth_provider == "google"
        assert user.password_hash is None
        assert user.google_sub == "google-123"
        assert access and refresh

    async def test_google_auth_existing_google_user_returns_tokens(self, db_session, test_settings):
        mock_resp = _mock_google_response(sub="existing-sub", email="existing@google.com")

        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings), \
             patch("app.auth.service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            instance = MockClient.return_value.__aenter__.return_value
            instance.post = AsyncMock(return_value=mock_resp)

            user1, _, _ = await GoogleAuthService.authenticate(
                db_session, "code-1", "http://localhost/callback"
            )
            user2, access, refresh = await GoogleAuthService.authenticate(
                db_session, "code-2", "http://localhost/callback"
            )

        assert user2.id == user1.id
        assert access and refresh

    async def test_google_auth_existing_email_links_account(self, db_session, test_settings):
        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings):
            local_user, _, _ = await AuthService.register(
                db_session, "linked@example.com", "Str0ngP@ss!", "Linked User"
            )
            assert local_user.google_sub is None

        mock_resp = _mock_google_response(sub="link-sub-123", email="linked@example.com", name="Linked User")

        with patch("app.auth.utils.settings", test_settings), \
             patch("app.auth.service.settings", test_settings), \
             patch("app.auth.service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            instance = MockClient.return_value.__aenter__.return_value
            instance.post = AsyncMock(return_value=mock_resp)

            linked_user, _, _ = await GoogleAuthService.authenticate(
                db_session, "link-code", "http://localhost/callback"
            )

        assert linked_user.id == local_user.id
        assert linked_user.google_sub == "link-sub-123"
