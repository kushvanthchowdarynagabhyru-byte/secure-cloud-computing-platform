"""
Encryption helpers for the Secure Cloud Computing Platform.

Design (envelope encryption, a common real-world cloud pattern):
  - Every uploaded file gets its OWN randomly generated Fernet key (the "data key").
  - The file is encrypted with that data key.
  - The data key itself is then encrypted with a single server-side MASTER_KEY
    and stored in the database (never stored in plaintext).
  - This means compromising one file's key does not expose other files, and the
    raw file bytes are never written to disk unencrypted.
"""

from cryptography.fernet import Fernet, InvalidToken


def generate_data_key() -> bytes:
    """Generate a fresh random encryption key for a single file."""
    return Fernet.generate_key()


def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Encrypt raw bytes with the given Fernet key."""
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_bytes(token: bytes, key: bytes) -> bytes:
    """Decrypt bytes previously produced by encrypt_bytes. Raises InvalidToken on failure."""
    f = Fernet(key)
    return f.decrypt(token)


def wrap_key(data_key: bytes, master_key: str) -> bytes:
    """Encrypt (wrap) a per-file data key using the server master key."""
    f = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
    return f.encrypt(data_key)


def unwrap_key(wrapped_key: bytes, master_key: str) -> bytes:
    """Decrypt (unwrap) a per-file data key using the server master key."""
    f = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
    return f.decrypt(wrapped_key)


__all__ = [
    "generate_data_key",
    "encrypt_bytes",
    "decrypt_bytes",
    "wrap_key",
    "unwrap_key",
    "InvalidToken",
]
