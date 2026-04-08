"""Unit tests for app/jira/encryption.py — Fernet encryption/decryption.

Tests per docs/db_hld.md § 5.1 (Jira Tokens — Fernet Encryption).
"""

from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken


_TEST_KEY = Fernet.generate_key()
_ALT_KEY = Fernet.generate_key()


def _make_test_settings(**overrides):
    from app.config import Settings

    defaults = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "SECRET_KEY": "test-secret",
        "JIRA_ENCRYPTION_KEY": _TEST_KEY.decode(),
        **overrides,
    }
    return Settings(**defaults)


_settings = _make_test_settings()


@pytest.fixture(autouse=True)
def _patch_encryption_module():
    """Re-initialise the module-level Fernet instance with the test key."""
    fernet = Fernet(_TEST_KEY)
    with patch("app.jira.encryption._fernet", fernet), \
         patch("app.jira.encryption.settings", _settings):
        yield


def test_encrypt_returns_bytes():
    from app.jira.encryption import encrypt_token

    result = encrypt_token("test")
    assert isinstance(result, bytes)


def test_decrypt_recovers_plaintext():
    from app.jira.encryption import decrypt_token, encrypt_token

    ciphertext = encrypt_token("my_token")
    assert decrypt_token(ciphertext) == "my_token"


def test_encrypt_produces_different_ciphertext_each_time():
    from app.jira.encryption import encrypt_token

    c1 = encrypt_token("same-value")
    c2 = encrypt_token("same-value")
    assert c1 != c2


def test_decrypt_with_wrong_key_raises():
    from app.jira.encryption import encrypt_token

    ciphertext = encrypt_token("secret-token")
    wrong_fernet = Fernet(_ALT_KEY)
    with pytest.raises(InvalidToken):
        wrong_fernet.decrypt(ciphertext)


def test_decrypt_corrupted_ciphertext_raises():
    from app.jira.encryption import decrypt_token

    with pytest.raises(Exception):
        decrypt_token(b"garbage-not-valid-ciphertext")


def test_encrypt_empty_string():
    from app.jira.encryption import decrypt_token, encrypt_token

    ciphertext = encrypt_token("")
    assert decrypt_token(ciphertext) == ""


def test_encrypt_long_token():
    from app.jira.encryption import decrypt_token, encrypt_token

    long_token = "A" * 2000
    ciphertext = encrypt_token(long_token)
    assert decrypt_token(ciphertext) == long_token
