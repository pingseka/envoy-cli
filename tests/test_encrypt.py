"""Tests for envoy.encrypt module."""

import pytest

try:
    from cryptography.fernet import Fernet  # noqa: F401
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

crypto = pytest.mark.skipif(not _CRYPTO_OK, reason="cryptography not installed")

from envoy.encrypt import (
    EncryptionError,
    MissingDependencyError,
    decrypt_env,
    decrypt_value,
    derive_key,
    encrypt_env,
    encrypt_value,
)


@crypto
class TestDeriveKey:
    def test_returns_bytes_tuple(self):
        key, salt = derive_key("secret")
        assert isinstance(key, bytes)
        assert isinstance(salt, bytes)

    def test_same_passphrase_and_salt_gives_same_key(self):
        key1, salt = derive_key("mysecret")
        key2, _ = derive_key("mysecret", salt=salt)
        assert key1 == key2

    def test_different_salts_give_different_keys(self):
        key1, _ = derive_key("mysecret")
        key2, _ = derive_key("mysecret")
        # Extremely unlikely to collide with random salts
        assert key1 != key2


@crypto
class TestEncryptDecryptValue:
    def test_roundtrip(self):
        original = "super_secret_value"
        token = encrypt_value(original, "passphrase123")
        result = decrypt_value(token, "passphrase123")
        assert result == original

    def test_encrypted_differs_from_plaintext(self):
        token = encrypt_value("hello", "pass")
        assert token != "hello"

    def test_wrong_passphrase_raises(self):
        token = encrypt_value("hello", "correct")
        with pytest.raises(EncryptionError, match="Decryption failed"):
            decrypt_value(token, "wrong")

    def test_invalid_format_raises(self):
        with pytest.raises(EncryptionError, match="Invalid encrypted value format"):
            decrypt_value("notvalidformat", "pass")

    def test_empty_string_roundtrip(self):
        token = encrypt_value("", "pass")
        assert decrypt_value(token, "pass") == ""


@crypto
class TestEncryptDecryptEnv:
    SAMPLE = {"DB_PASSWORD": "secret", "API_KEY": "key123", "HOST": "localhost"}

    def test_full_roundtrip(self):
        enc = encrypt_env(self.SAMPLE, "mypass")
        dec = decrypt_env(enc, "mypass")
        assert dec == self.SAMPLE

    def test_selective_encrypt(self):
        enc = encrypt_env(self.SAMPLE, "mypass", keys=["DB_PASSWORD"])
        assert enc["HOST"] == "localhost"  # unchanged
        assert enc["DB_PASSWORD"] != "secret"

    def test_selective_decrypt(self):
        enc = encrypt_env(self.SAMPLE, "mypass", keys=["API_KEY"])
        dec = decrypt_env(enc, "mypass", keys=["API_KEY"])
        assert dec["API_KEY"] == "key123"

    def test_missing_key_ignored(self):
        enc = encrypt_env(self.SAMPLE, "mypass", keys=["NONEXISTENT"])
        assert enc == self.SAMPLE
