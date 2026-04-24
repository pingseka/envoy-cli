"""Tests for the .env file parser module."""

import os
import tempfile
import pytest

from envoy.parser import parse_env_file, serialize_env, _is_secret_key


def write_temp_env(content: str) -> str:
    """Write content to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    tmp.write(content)
    tmp.close()
    return tmp.name


class TestParseEnvFile:
    def test_simple_key_value(self):
        path = write_temp_env("FOO=bar\nBAZ=qux\n")
        result = parse_env_file(path)
        assert result == {"FOO": "bar", "BAZ": "qux"}
        os.unlink(path)

    def test_skips_comments(self):
        path = write_temp_env("# this is a comment\nKEY=value\n")
        result = parse_env_file(path)
        assert "# this is a comment" not in result
        assert result["KEY"] == "value"
        os.unlink(path)

    def test_skips_blank_lines(self):
        path = write_temp_env("\nKEY=value\n\n")
        result = parse_env_file(path)
        assert result == {"KEY": "value"}
        os.unlink(path)

    def test_double_quoted_value(self):
        path = write_temp_env('DB_URL="postgres://localhost/db"\n')
        result = parse_env_file(path)
        assert result["DB_URL"] == "postgres://localhost/db"
        os.unlink(path)

    def test_single_quoted_value(self):
        path = write_temp_env("MSG='hello world'\n")
        result = parse_env_file(path)
        assert result["MSG"] == "hello world"
        os.unlink(path)

    def test_inline_comment_stripped(self):
        path = write_temp_env("PORT=8080 # default port\n")
        result = parse_env_file(path)
        assert result["PORT"] == "8080"
        os.unlink(path)

    def test_empty_value(self):
        path = write_temp_env("EMPTY=\n")
        result = parse_env_file(path)
        assert result["EMPTY"] == ""
        os.unlink(path)


class TestSerializeEnv:
    def test_basic_serialization(self):
        result = serialize_env({"FOO": "bar", "NUM": "42"})
        assert "FOO=bar" in result
        assert "NUM=42" in result

    def test_mask_secrets(self):
        env = {"API_KEY": "super-secret", "HOST": "localhost"}
        result = serialize_env(env, mask_secrets=True)
        assert "API_KEY=****" in result
        assert "HOST=localhost" in result

    def test_quotes_values_with_spaces(self):
        result = serialize_env({"MSG": "hello world"})
        assert 'MSG="hello world"' in result


class TestIsSecretKey:
    def test_detects_secret(self):
        assert _is_secret_key("SECRET_KEY") is True
        assert _is_secret_key("DB_PASSWORD") is True
        assert _is_secret_key("AUTH_TOKEN") is True
        assert _is_secret_key("GITHUB_API_KEY") is True

    def test_non_secret(self):
        assert _is_secret_key("HOST") is False
        assert _is_secret_key("PORT") is False
        assert _is_secret_key("APP_ENV") is False
