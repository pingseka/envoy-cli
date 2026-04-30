"""Tests for envoy.defaults and envoy.cli_defaults."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.defaults import DefaultStatus, apply_defaults
from envoy.parser import parse_env_file


# ---------------------------------------------------------------------------
# Unit tests — apply_defaults
# ---------------------------------------------------------------------------

class TestApplyDefaults:
    def test_applies_missing_key(self):
        env: dict[str, str] = {"A": "1"}
        result = apply_defaults(env, {"B": "2"})
        assert env["B"] == "2"
        assert len(result.applied()) == 1
        assert result.applied()[0].key == "B"

    def test_skips_existing_key(self):
        env: dict[str, str] = {"A": "original"}
        result = apply_defaults(env, {"A": "default"})
        assert env["A"] == "original"
        assert len(result.skipped()) == 1

    def test_mixed_applied_and_skipped(self):
        env: dict[str, str] = {"X": "existing"}
        result = apply_defaults(env, {"X": "ignore", "Y": "new"})
        assert len(result.applied()) == 1
        assert len(result.skipped()) == 1
        assert env["Y"] == "new"
        assert env["X"] == "existing"

    def test_empty_defaults_leaves_env_unchanged(self):
        env: dict[str, str] = {"A": "1"}
        result = apply_defaults(env, {})
        assert env == {"A": "1"}
        assert result.entries == []

    def test_summary_string(self):
        env: dict[str, str] = {"A": "1"}
        result = apply_defaults(env, {"A": "x", "B": "y"})
        summary = result.summary()
        assert "1 default(s) applied" in summary
        assert "1 already present" in summary

    def test_entry_str_applied(self):
        env: dict[str, str] = {}
        result = apply_defaults(env, {"FOO": "bar"})
        assert "[+]" in str(result.entries[0])
        assert "applied" in str(result.entries[0])

    def test_entry_str_skipped(self):
        env: dict[str, str] = {"FOO": "bar"}
        result = apply_defaults(env, {"FOO": "baz"})
        assert "[=]" in str(result.entries[0])
        assert "skipped" in str(result.entries[0])


# ---------------------------------------------------------------------------
# CLI tests — cmd_defaults
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    _write(p, "EXISTING=hello\n")
    return p


def make_args(file: str, defaults: list[str], write: bool = False):
    import argparse
    ns = argparse.Namespace(file=file, defaults=defaults, write=write)
    return ns


class TestCmdDefaults:
    def test_exits_zero_on_success(self, tmp_env: Path):
        from envoy.cli_defaults import cmd_defaults
        rc = cmd_defaults(make_args(str(tmp_env), ["NEW=world"]))
        assert rc == 0

    def test_applies_missing_key_to_file(self, tmp_env: Path):
        from envoy.cli_defaults import cmd_defaults
        cmd_defaults(make_args(str(tmp_env), ["NEW=world"], write=True))
        env = parse_env_file(str(tmp_env))
        assert env["NEW"] == "world"

    def test_does_not_overwrite_existing_key(self, tmp_env: Path):
        from envoy.cli_defaults import cmd_defaults
        cmd_defaults(make_args(str(tmp_env), ["EXISTING=changed"], write=True))
        env = parse_env_file(str(tmp_env))
        assert env["EXISTING"] == "hello"

    def test_missing_file_returns_one(self, tmp_path: Path):
        from envoy.cli_defaults import cmd_defaults
        rc = cmd_defaults(make_args(str(tmp_path / "ghost.env"), ["A=1"]))
        assert rc == 1

    def test_invalid_default_format_returns_one(self, tmp_env: Path):
        from envoy.cli_defaults import cmd_defaults
        rc = cmd_defaults(make_args(str(tmp_env), ["NODEQUALS"]))
        assert rc == 1

    def test_no_defaults_returns_one(self, tmp_env: Path):
        from envoy.cli_defaults import cmd_defaults
        rc = cmd_defaults(make_args(str(tmp_env), []))
        assert rc == 1
