"""Unit tests for SQLAlchemy model constraints and relationships.

Tests per docs/db_hld.md §§ 3.1–3.4.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.exc import IntegrityError

from app.models.api_key import ApiKey
from app.models.jira_connection import JiraConnection
from app.models.ticket import Ticket
from app.models.user import User


_fernet = Fernet(Fernet.generate_key())


def _make_user(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": "$2b$12$fakehash",
        "full_name": "Test User",
        "auth_provider": "local",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return User(**defaults)


def _make_connection(user_id, **kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "cloud_id": "cloud-" + uuid.uuid4().hex[:6],
        "site_url": "https://test.atlassian.net",
        "access_token_enc": _fernet.encrypt(b"at"),
        "refresh_token_enc": _fernet.encrypt(b"rt"),
        "token_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return JiraConnection(**defaults)


# ── Users Model ────────────────────────────────────────────────────────────


class TestUserModel:
    async def test_user_email_unique_constraint(self, db_session):
        u1 = _make_user(email="unique@test.com")
        u2 = _make_user(email="unique@test.com")
        db_session.add(u1)
        await db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_user_google_sub_unique_constraint(self, db_session):
        u1 = _make_user(google_sub="gsub-same")
        u2 = _make_user(google_sub="gsub-same")
        db_session.add(u1)
        await db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_user_password_hash_nullable(self, db_session):
        u = _make_user(password_hash=None)
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        assert u.password_hash is None

    async def test_user_auth_provider_defaults_to_local(self, db_session):
        u = User(
            id=uuid.uuid4(),
            email=f"default-{uuid.uuid4().hex[:6]}@test.com",
            password_hash="$2b$12$hash",
            full_name="Default Provider",
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        assert u.auth_provider == "local"

    async def test_user_created_at_auto_set(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        assert u.created_at is not None


# ── JiraConnections Model ──────────────────────────────────────────────────


class TestJiraConnectionModel:
    async def test_jira_connection_user_id_unique(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        c1 = _make_connection(u.id)
        db_session.add(c1)
        await db_session.commit()

        c2 = _make_connection(u.id)
        db_session.add(c2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_jira_connection_fk_to_users(self, db_session):
        fake_id = uuid.uuid4()
        c = _make_connection(fake_id)
        db_session.add(c)
        with pytest.raises(IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_jira_connection_stores_bytea_tokens(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        enc_access = _fernet.encrypt(b"access-token-bytes")
        enc_refresh = _fernet.encrypt(b"refresh-token-bytes")
        c = _make_connection(u.id, access_token_enc=enc_access, refresh_token_enc=enc_refresh)
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        assert isinstance(c.access_token_enc, bytes)
        assert isinstance(c.refresh_token_enc, bytes)


# ── ApiKeys Model ──────────────────────────────────────────────────────────


class TestApiKeyModel:
    async def test_api_key_hash_unique(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        k1 = ApiKey(
            id=uuid.uuid4(), user_id=u.id, name="k1",
            key_hash="samehash", key_prefix="ihub_live_ab",
            created_at=datetime.now(timezone.utc),
        )
        k2 = ApiKey(
            id=uuid.uuid4(), user_id=u.id, name="k2",
            key_hash="samehash", key_prefix="ihub_live_cd",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(k1)
        await db_session.commit()
        db_session.add(k2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_api_key_is_active_defaults_true(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        k = ApiKey(
            id=uuid.uuid4(), user_id=u.id, name="active-default",
            key_hash=uuid.uuid4().hex, key_prefix="ihub_live_xx",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(k)
        await db_session.commit()
        await db_session.refresh(k)
        assert k.is_active is True

    async def test_api_key_last_used_at_nullable(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        k = ApiKey(
            id=uuid.uuid4(), user_id=u.id, name="nullable",
            key_hash=uuid.uuid4().hex, key_prefix="ihub_live_yy",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(k)
        await db_session.commit()
        await db_session.refresh(k)
        assert k.last_used_at is None


# ── Tickets Model ──────────────────────────────────────────────────────────


class TestTicketModel:
    async def test_ticket_issue_type_defaults_to_task(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        c = _make_connection(u.id)
        db_session.add(c)
        await db_session.commit()

        t = Ticket(
            id=uuid.uuid4(),
            user_id=u.id,
            jira_connection_id=c.id,
            jira_ticket_key="DEF-1",
            jira_ticket_url="https://x.atlassian.net/browse/DEF-1",
            project_key="DEF",
            summary="Default issue type",
            source="ui",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(t)
        await db_session.commit()
        await db_session.refresh(t)
        assert t.issue_type == "Task"

    async def test_ticket_fk_to_users(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()
        c = _make_connection(u.id)
        db_session.add(c)
        await db_session.commit()

        t = Ticket(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # non-existent user
            jira_connection_id=c.id,
            jira_ticket_key="FK-1",
            jira_ticket_url="https://x/FK-1",
            project_key="FK",
            summary="FK test",
            source="ui",
            issue_type="Task",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(t)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_ticket_fk_to_jira_connections(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        t = Ticket(
            id=uuid.uuid4(),
            user_id=u.id,
            jira_connection_id=uuid.uuid4(),  # non-existent connection
            jira_ticket_key="FK-2",
            jira_ticket_url="https://x/FK-2",
            project_key="FK",
            summary="FK test conn",
            source="ui",
            issue_type="Task",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(t)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()


# ── Relationships ──────────────────────────────────────────────────────────


class TestRelationships:
    async def test_user_has_jira_connection_relationship(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        c = _make_connection(u.id)
        db_session.add(c)
        await db_session.commit()

        await db_session.refresh(u, ["jira_connection"])
        assert u.jira_connection is not None
        assert u.jira_connection.cloud_id == c.cloud_id

    async def test_user_has_api_keys_relationship(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        k1 = ApiKey(user_id=u.id, name="k1", key_hash=uuid.uuid4().hex, key_prefix="ihub_live_11")
        k2 = ApiKey(user_id=u.id, name="k2", key_hash=uuid.uuid4().hex, key_prefix="ihub_live_22")
        db_session.add_all([k1, k2])
        await db_session.commit()

        await db_session.refresh(u, ["api_keys"])
        assert len(u.api_keys) == 2

    async def test_user_has_tickets_relationship(self, db_session):
        u = _make_user()
        db_session.add(u)
        await db_session.commit()

        c = _make_connection(u.id)
        db_session.add(c)
        await db_session.commit()

        t = Ticket(
            user_id=u.id,
            jira_connection_id=c.id,
            jira_ticket_key="REL-1",
            jira_ticket_url="https://x/REL-1",
            project_key="REL",
            summary="Relationship test",
            source="ui",
            issue_type="Task",
        )
        db_session.add(t)
        await db_session.commit()

        await db_session.refresh(u, ["tickets"])
        assert len(u.tickets) == 1
        assert u.tickets[0].jira_ticket_key == "REL-1"
