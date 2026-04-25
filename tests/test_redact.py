"""Tests for envoy.redact module."""

import pytest

from envoy.redact import (
    REDACTED_PLACEHOLDER,
    RedactResult,
    _partial_mask,
    redact_env,
)


class TestPartialMask:
    def test_short_value_returns_placeholder(self):
        assert _partial_mask("abc") == REDACTED_PLACEHOLDER

    def test_long_value_shows_edges(self):
        result = _partial_mask("abcdefghij")
        assert result.startswith("ab")
        assert result.endswith("ij")
        assert "*" in result

    def test_exactly_min_length_shows_edges(self):
        result = _partial_mask("abcdefgh")  # length == 8
        assert result.startswith("ab")
        assert result.endswith("gh")


class TestRedactEnv:
    def test_non_secret_keys_unchanged(self):
        env = {"APP_NAME": "myapp", "PORT": "8080"}
        result = redact_env(env)
        assert result.redacted["APP_NAME"] == "myapp"
        assert result.redacted["PORT"] == "8080"
        assert result.redacted_keys == []

    def test_secret_keys_are_masked(self):
        env = {"SECRET_KEY": "supersecret", "API_KEY": "abc123"}
        result = redact_env(env)
        assert result.redacted["SECRET_KEY"] == REDACTED_PLACEHOLDER
        assert result.redacted["API_KEY"] == REDACTED_PLACEHOLDER
        assert set(result.redacted_keys) == {"SECRET_KEY", "API_KEY"}

    def test_password_key_is_masked(self):
        env = {"DB_PASSWORD": "hunter2"}
        result = redact_env(env)
        assert result.redacted["DB_PASSWORD"] == REDACTED_PLACEHOLDER

    def test_token_key_is_masked(self):
        env = {"GITHUB_TOKEN": "ghp_abc123"}
        result = redact_env(env)
        assert result.redacted["GITHUB_TOKEN"] == REDACTED_PLACEHOLDER

    def test_original_preserved(self):
        env = {"SECRET_KEY": "mysecret"}
        result = redact_env(env)
        assert result.original["SECRET_KEY"] == "mysecret"

    def test_extra_keys_are_masked(self):
        env = {"MY_CUSTOM": "value123", "NORMAL": "hello"}
        result = redact_env(env, extra_keys=["MY_CUSTOM"])
        assert result.redacted["MY_CUSTOM"] == REDACTED_PLACEHOLDER
        assert result.redacted["NORMAL"] == "hello"

    def test_extra_keys_case_insensitive(self):
        env = {"MY_CUSTOM": "value123"}
        result = redact_env(env, extra_keys=["my_custom"])
        assert result.redacted["MY_CUSTOM"] == REDACTED_PLACEHOLDER

    def test_partial_mode_shows_edges(self):
        env = {"SECRET_KEY": "abcdefghij"}
        result = redact_env(env, partial=True)
        val = result.redacted["SECRET_KEY"]
        assert val != REDACTED_PLACEHOLDER
        assert val.startswith("ab")
        assert val.endswith("ij")

    def test_summary_no_redactions(self):
        env = {"PORT": "8080"}
        result = redact_env(env)
        assert result.summary() == "No secrets redacted."

    def test_summary_with_redactions(self):
        env = {"API_KEY": "abc", "PORT": "8080"}
        result = redact_env(env)
        assert "1 secret(s) redacted" in result.summary()
        assert "API_KEY" in result.summary()
