"""Tests for envoy.trim."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from envoy.trim import TrimStatus, trim_env


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(tmp_dir):
    p = tmp_dir / ".env"
    _write(p, "KEY1=  hello  \nKEY2=world\nKEY3=  spaced\n")
    return p


class TestTrimEnv:
    def test_trims_padded_value(self, env_file):
        result = trim_env(env_file)
        entry = next(e for e in result.entries if e.key == "KEY1")
        assert entry.trimmed == "hello"
        assert entry.status == TrimStatus.TRIMMED

    def test_unchanged_when_no_whitespace(self, env_file):
        result = trim_env(env_file)
        entry = next(e for e in result.entries if e.key == "KEY2")
        assert entry.status == TrimStatus.UNCHANGED
        assert entry.trimmed == "world"

    def test_trims_leading_whitespace_only(self, env_file):
        result = trim_env(env_file)
        entry = next(e for e in result.entries if e.key == "KEY3")
        assert entry.trimmed == "spaced"
        assert entry.status == TrimStatus.TRIMMED

    def test_result_env_has_trimmed_values(self, env_file):
        result = trim_env(env_file)
        assert result.env["KEY1"] == "hello"
        assert result.env["KEY2"] == "world"

    def test_trimmed_list_contains_only_changed(self, env_file):
        result = trim_env(env_file)
        trimmed_keys = [e.key for e in result.trimmed()]
        assert "KEY1" in trimmed_keys
        assert "KEY2" not in trimmed_keys

    def test_summary_string(self, env_file):
        result = trim_env(env_file)
        s = result.summary()
        assert "trimmed" in s
        assert "unchanged" in s

    def test_keys_filter_limits_scope(self, tmp_dir):
        p = tmp_dir / ".env"
        _write(p, "A=  value  \nB=  other  \n")
        result = trim_env(p, keys=["A"])
        assert result.env["A"] == "value"
        assert result.env["B"] == "  other  "

    def test_write_persists_trimmed_values(self, tmp_dir):
        p = tmp_dir / ".env"
        _write(p, "X=  hello  \nY=world\n")
        trim_env(p, write=True)
        content = p.read_text(encoding="utf-8")
        assert "  hello  " not in content
        assert "hello" in content

    def test_no_keys_trims_all(self, tmp_dir):
        p = tmp_dir / ".env"
        _write(p, "A=  1  \nB=  2  \n")
        result = trim_env(p)
        assert all(e.trimmed == e.trimmed.strip() for e in result.entries)

    def test_entry_str_trimmed(self, env_file):
        result = trim_env(env_file)
        entry = next(e for e in result.entries if e.key == "KEY1")
        s = str(entry)
        assert "->" in s

    def test_entry_str_unchanged(self, env_file):
        result = trim_env(env_file)
        entry = next(e for e in result.entries if e.key == "KEY2")
        assert "unchanged" in str(entry)
