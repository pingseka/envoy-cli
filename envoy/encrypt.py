"""Encryption and decryption utilities for secret values in .env files."""

import base64
import hashlib
import os
from typing import Dict

try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class MissingDependencyError(EncryptionError):
    """Raised when the cryptography package is not installed."""


def _require_cryptography() -> None:
    if not _CRYPTOGRAPHY_AVAILABLE:
        raise MissingDependencyError(
            "The 'cryptography' package is required for encryption. "
            "Install it with: pip install cryptography"
        )


def derive_key(passphrase: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Derive a Fernet-compatible key from a passphrase using PBKDF2.

    Returns (key, salt) so the salt can be stored alongside the ciphertext.
    """
    _require_cryptography()
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, iterations=200_000)
    key = base64.urlsafe_b64encode(dk)
    return key, salt


def encrypt_value(plaintext: str, passphrase: str) -> str:
    """Encrypt a single string value. Returns a base64-encoded token that
    embeds the salt so it can be decrypted with only the passphrase.
    """
    _require_cryptography()
    key, salt = derive_key(passphrase)
    f = Fernet(key)
    token = f.encrypt(plaintext.encode())
    # Prefix: base64(salt) + ":" + base64(token)
    encoded = base64.urlsafe_b64encode(salt).decode() + ":" + token.decode()
    return encoded


def decrypt_value(encoded: str, passphrase: str) -> str:
    """Decrypt a value previously produced by encrypt_value."""
    _require_cryptography()
    try:
        salt_b64, token = encoded.split(":", 1)
    except ValueError:
        raise EncryptionError("Invalid encrypted value format.")
    salt = base64.urlsafe_b64decode(salt_b64)
    key, _ = derive_key(passphrase, salt=salt)
    f = Fernet(key)
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise EncryptionError("Decryption failed: wrong passphrase or corrupted data.") from exc


def encrypt_env(env: Dict[str, str], passphrase: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return a new env dict with specified keys (or all keys) encrypted."""
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for k in targets:
        if k in result:
            result[k] = encrypt_value(result[k], passphrase)
    return result


def decrypt_env(env: Dict[str, str], passphrase: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return a new env dict with specified keys (or all keys) decrypted."""
    result = dict(env)
    targets = keys if keys is not None else list(env.keys())
    for k in targets:
        if k in result:
            result[k] = decrypt_value(result[k], passphrase)
    return result
