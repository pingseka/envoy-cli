"""Tests for envoy.inject."""
from __future__ import annotations

import pytest
from pathlib import Path

from envoy.inject import inject_env, InjectStatus
from envoy.parser import parse_env_file


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def env_file(tmp_dir: Path) -> Path:
    return _write(tmp_dir / ".env", "EXISTING=hello\nOTHER=world\n")


class TestInjectEnv:
    def test_adds_new_key(self, env_file: Path) -> None:
        result = inject_env(env_file, {"NEW_KEY": "newval"})
        assert any(e.key == "NEW_KEY" and e.status == InjectStatus.ADDED for e in result.entries)
        parsed = parse_env_file(env_file)
        assert parsed["NEW_KEY"] == "newval"

    def test_skips_existing_key_by_default(self, env_file: Path) -> None:
        result = inject_env(env_file, {"EXISTING": "changed"})
        assert any(e.key == "EXISTING" and e.status == InjectStatus.SKIPPED for e in result.entries)
        parsed = parse_env_file(env_file)
        assert parsed["EXISTING"] == "hello"

    def test_updates_existing_key_when_overwrite(self, env_file: Path) -> None:
        result = inject_env(env_file, {"EXISTING": "updated"}, overwrite=True)
        assert any(e.key == "EXISTING" and e.status == InjectStatus.UPDATED for e in result.entries)
        parsed = parse_env_file(env_file)
        assert parsed["EXISTING"] == "updated"

    def test_creates_file_if_missing(self, tmp_dir: Path) -> None:
        new_file = tmp_dir / "new.env"
        assert not new_file.exists()
        inject_env(new_file, {"FOO": "bar"})
        assert new_file.exists()
        assert parse_env_file(new_file)["FOO"] == "bar"

    def test_summary_counts(self, env_file: Path) -> None:
        result = inject_env(
            env_file,
            {"EXISTING": "x", "OTHER": "y", "BRAND_NEW": "z"},
            overwrite=False,
        )
        assert len(result.added()) == 1
        assert len(result.skipped()) == 2
        assert len(result.updated()) == 0

    def test_summary_string(self, env_file: Path) -> None:
        result = inject_env(env_file, {"EXISTING": "x", "FRESH": "y"}, overwrite=True)
        summary = result.summary()
        assert "added" in summary
        assert "updated" in summary
        assert "skipped" in summary

    def test_entry_str(self, env_file: Path) -> None:
        result = inject_env(env_file, {"BRAND_NEW": "val"})
        entry = result.added()[0]
        assert "ADDED" in str(entry)
        assert "BRAND_NEW" in str(entry)

    def test_preserves_untouched_keys(self, env_file: Path) -> None:
        inject_env(env_file, {"NEW": "1"})
        parsed = parse_env_file(env_file)
        assert parsed["OTHER"] == "world"
        assert parsed["EXISTING"] == "hello"
