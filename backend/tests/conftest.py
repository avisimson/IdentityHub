"""Shared pytest fixtures for the IdentityHub backend test suite.

Provides:
- ``test_settings``  – patched app settings with test-safe values
- ``test_engine``    – async SQLAlchemy engine for the test database
- ``db_session``     – per-test async session with full table isolation
- ``async_client``   – httpx client wired to the FastAPI app
- ``test_user``      – factory that inserts a user row and returns the ORM object
- ``auth_headers``   – valid JWT ``Authorization`` header for a test user
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.utils import create_access_token, hash_password
from app.config import Settings

# Import Base *from app.models* so every model is registered on the metadata.
from app.models import Base


# ---------------------------------------------------------------------------
# Test-safe settings
# ---------------------------------------------------------------------------

_TEST_SECRET_KEY = "test-secret-key-0123456789abcdef0123456789abcdef"
_TEST_FERNET_KEY = Fernet.generate_key().decode()
_TEST_JIRA_ENCRYPTION_KEY = _TEST_FERNET_KEY


def _build_test_database_url() -> str:
    """Derive the test database URL.

    Priority:
    1. ``TEST_DATABASE_URL`` environment variable (explicit override).
    2. ``DATABASE_URL`` with the database name suffixed by ``_test``.
    3. In-memory SQLite via ``aiosqlite`` (CI fallback).
    """
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit

    prod_url = os.environ.get("DATABASE_URL", "")
    if prod_url and "postgresql" in prod_url:
        if "/" in prod_url.rsplit("@", 1)[-1]:
            base, _db_name = prod_url.rsplit("/", 1)
            return f"{base}/{_db_name}_test"
        return f"{prod_url}_test"

    return "sqlite+aiosqlite://"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Return a ``Settings`` instance with deterministic, test-safe values."""
    return Settings(
        DATABASE_URL=_build_test_database_url(),
        SECRET_KEY=_TEST_SECRET_KEY,
        JIRA_ENCRYPTION_KEY=_TEST_JIRA_ENCRYPTION_KEY,
        JIRA_CLIENT_ID="test-jira-client-id",
        JIRA_CLIENT_SECRET="test-jira-client-secret",
        GOOGLE_CLIENT_ID="test-google-client-id",
        GOOGLE_CLIENT_SECRET="test-google-client-secret",
    )


# ---------------------------------------------------------------------------
# Database engine & session
# ---------------------------------------------------------------------------


def _register_sqlite_functions(dbapi_conn, connection_record):
    """Register PostgreSQL-compatible functions and enable FK enforcement for SQLite."""
    dbapi_conn.create_function(
        "gen_random_uuid", 0, lambda: str(uuid.uuid4())
    )
    dbapi_conn.create_function(
        "now", 0, lambda: datetime.now(timezone.utc).isoformat()
    )
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


@pytest.fixture(scope="session")
def test_engine(test_settings: Settings):
    """Create an ``AsyncEngine`` pointed at the test database."""
    connect_args: dict[str, Any] = {}
    is_sqlite = test_settings.DATABASE_URL.startswith("sqlite")
    if is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        connect_args=connect_args,
    )

    if is_sqlite:
        event.listen(engine.sync_engine, "connect", _register_sqlite_functions)

    return engine


def _set_sqlite_client_defaults(mapper, connection, target):
    """Provide client-side defaults for columns that use PostgreSQL server_default."""
    if getattr(target, "id", None) is None:
        target.id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    if hasattr(target, "created_at") and target.created_at is None:
        target.created_at = now
    if hasattr(target, "updated_at") and target.updated_at is None:
        target.updated_at = now


@pytest.fixture(scope="session", autouse=True)
def _sqlite_model_defaults(test_settings):
    """Register before_insert listeners for SQLite that supply client-side defaults."""
    if not test_settings.DATABASE_URL.startswith("sqlite"):
        return

    from app.models.user import User
    from app.models.api_key import ApiKey
    from app.models.jira_connection import JiraConnection
    from app.models.ticket import Ticket

    for model in (User, ApiKey, JiraConnection, Ticket):
        event.listen(model, "init", _init_sqlite_defaults, propagate=True)
        event.listen(model, "before_insert", _set_sqlite_client_defaults, propagate=True)


def _init_sqlite_defaults(target, args, kwargs):
    """No-op init listener — actual defaults set in before_insert."""
    pass


@pytest.fixture()
async def db_session(test_engine, test_settings) -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` with fresh tables for every test.

    Tables are created before the test and dropped after, guaranteeing full
    isolation between tests.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        with patch("app.config.settings", test_settings), \
             patch("app.database.async_session_factory", session_factory):
            yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest.fixture()
async def async_client(
    db_session: AsyncSession,
    test_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an ``httpx.AsyncClient`` bound to the FastAPI app.

    The ``get_db`` dependency is overridden so every request uses the
    test ``db_session``, and ``app.config.settings`` is patched with
    test-safe values.  The lifespan is disabled to avoid running Alembic
    migrations during tests.
    """
    with patch("app.config.settings", test_settings):
        from app.database import get_db
        from app.main import app

        async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = _override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# User factory & auth helpers
# ---------------------------------------------------------------------------

_DEFAULT_PASSWORD = "Test1234!"


@pytest.fixture()
def test_user(db_session: AsyncSession):
    """Factory fixture: call it to create a user in the test database.

    Usage::

        user = await test_user()               # defaults
        user = await test_user(email="a@b.c")  # custom email
    """

    async def _create(
        *,
        email: str | None = None,
        password: str = _DEFAULT_PASSWORD,
        full_name: str = "Test User",
        auth_provider: str = "local",
    ):
        from app.models.user import User

        user = User(
            id=uuid.uuid4(),
            email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password(password),
            full_name=full_name,
            auth_provider=auth_provider,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest.fixture()
async def auth_headers(test_user, test_settings) -> dict[str, str]:
    """Create a test user and return ``Authorization`` headers with a valid JWT.

    The token is generated with the test ``SECRET_KEY`` so the app (also
    patched with the same key) will accept it.
    """
    with patch("app.config.settings", test_settings), \
         patch("app.auth.utils.settings", test_settings):
        user = await test_user()
        token = create_access_token(str(user.id), user.email)
    return {"Authorization": f"Bearer {token}"}
