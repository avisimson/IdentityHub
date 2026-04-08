"""Fernet encryption/decryption for Jira OAuth tokens.

Tokens are encrypted at rest (BYTEA in DB) and decrypted in-memory only
when making Jira API calls.  They must never be logged or returned to
the client.

Key: JIRA_ENCRYPTION_KEY env var — a base64-encoded 32-byte key suitable
for cryptography.fernet.Fernet.
"""

from cryptography.fernet import Fernet

from app.config import settings

_fernet = Fernet(settings.JIRA_ENCRYPTION_KEY)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a plaintext token string and return ciphertext bytes
    suitable for storage in a BYTEA column."""
    return _fernet.encrypt(plaintext.encode("utf-8"))


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt ciphertext bytes back to the original plaintext token string."""
    return _fernet.decrypt(ciphertext).decode("utf-8")
