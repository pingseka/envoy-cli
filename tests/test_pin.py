"""Tests for envoy.pin."""

import os
import tempfile

import pytest

from envoy.pin import (
    PinViolationKind,
    PinResult,
    check_pins,
)


@pytest.fixture
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)

    return _write


class TestCheckPins:
    def test_all_satisfied_returns_ok(self, tmp_env):
        path = tmp_env("APP_ENV=production\nDEBUG=false\n")
        result = check_pins(path, {"APP_ENV": "production", "DEBUG": "false"})
        assert result.ok

    def test_missing_key_reports_violation(self, tmp_env):
        path = tmp_env("APP_ENV=production\n")
        result = check_pins(path, {"SECRET_KEY": None})
        assert not result.ok
        assert result.violations[0].kind == PinViolationKind.MISSING
        assert result.violations[0].key == "SECRET_KEY"

    def test_value_mismatch_reports_violation(self, tmp_env):
        path = tmp_env("APP_ENV=staging\n")
        result = check_pins(path, {"APP_ENV": "production"})
        assert not result.ok
        v = result.violations[0]
        assert v.kind == PinViolationKind.VALUE_MISMATCH
        assert v.expected == "production"
        assert v.actual == "staging"

    def test_none_value_only_checks_presence(self, tmp_env):
        path = tmp_env("DB_URL=postgres://localhost/mydb\n")
        result = check_pins(path, {"DB_URL": None})
        assert result.ok

    def test_regex_pin_passes(self, tmp_env):
        path = tmp_env("PORT=8080\n")
        result = check_pins(path, {"PORT": "re:[0-9]+"})
        assert result.ok

    def test_regex_pin_fails(self, tmp_env):
        path = tmp_env("PORT=abc\n")
        result = check_pins(path, {"PORT": "re:[0-9]+"})
        assert not result.ok
        assert result.violations[0].kind == PinViolationKind.PATTERN_MISMATCH

    def test_multiple_violations_collected(self, tmp_env):
        path = tmp_env("APP_ENV=staging\n")
        result = check_pins(
            path,
            {"APP_ENV": "production", "MISSING_KEY": None},
        )
        assert len(result.violations) == 2

    def test_empty_pins_always_ok(self, tmp_env):
        path = tmp_env("APP_ENV=staging\n")
        result = check_pins(path, {})
        assert result.ok

    def test_summary_ok_message(self, tmp_env):
        path = tmp_env("APP_ENV=production\n")
        result = check_pins(path, {"APP_ENV": "production"})
        assert "satisfied" in result.summary()

    def test_summary_lists_violations(self, tmp_env):
        path = tmp_env("APP_ENV=staging\n")
        result = check_pins(path, {"APP_ENV": "production"})
        assert "APP_ENV" in result.summary()
