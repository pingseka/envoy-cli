"""Tests for envoy.sync module."""

import pytest
from pathlib import Path

from envoy.sync import (
    sync_env_files,
    write_synced_env,
    SyncConflict,
    SyncIssue,
    SyncResult,
)


@pytest.fixture
def tmp_env(tmp_path):
    """Factory that writes a dict to a temp .env file."""
    def _write(name: str, data: dict) -> Path:
        p = tmp_path / name
        lines = [f"{k}={v}" for k, v in data.items()]
        p.write_text("\n".join(lines) + "\n")
        return p
    return _write


class TestSyncEnvFiles:
    def test_no_conflicts_when_identical(self, tmp_env):
        src = tmp_env("source.env", {"A": "1", "B": "2"})
        tgt = tmp_env("target.env", {"A": "1", "B": "2"})
        result = sync_env_files(src, tgt)
        assert not result.has_conflicts
        assert result.merged == {"A": "1", "B": "2"}

    def test_detects_missing_in_target(self, tmp_env):
        src = tmp_env("source.env", {"A": "1", "NEW": "hello"})
        tgt = tmp_env("target.env", {"A": "1"})
        result = sync_env_files(src, tgt)
        assert result.has_conflicts
        conflicts = {i.conflict for i in result.issues}
        assert SyncConflict.MISSING_IN_TARGET in conflicts

    def test_missing_key_added_by_default(self, tmp_env):
        src = tmp_env("source.env", {"A": "1", "NEW": "hello"})
        tgt = tmp_env("target.env", {"A": "1"})
        result = sync_env_files(src, tgt, add_missing=True)
        assert "NEW" in result.merged
        assert result.merged["NEW"] == "hello"

    def test_missing_key_not_added_when_disabled(self, tmp_env):
        src = tmp_env("source.env", {"A": "1", "NEW": "hello"})
        tgt = tmp_env("target.env", {"A": "1"})
        result = sync_env_files(src, tgt, add_missing=False)
        assert "NEW" not in result.merged

    def test_detects_value_differs(self, tmp_env):
        src = tmp_env("source.env", {"A": "new_val"})
        tgt = tmp_env("target.env", {"A": "old_val"})
        result = sync_env_files(src, tgt)
        assert any(i.conflict == SyncConflict.VALUE_DIFFERS for i in result.issues)

    def test_overwrite_applies_source_value(self, tmp_env):
        src = tmp_env("source.env", {"A": "new_val"})
        tgt = tmp_env("target.env", {"A": "old_val"})
        result = sync_env_files(src, tgt, overwrite=True)
        assert result.merged["A"] == "new_val"

    def test_no_overwrite_keeps_target_value(self, tmp_env):
        src = tmp_env("source.env", {"A": "new_val"})
        tgt = tmp_env("target.env", {"A": "old_val"})
        result = sync_env_files(src, tgt, overwrite=False)
        assert result.merged["A"] == "old_val"

    def test_detects_missing_in_source(self, tmp_env):
        src = tmp_env("source.env", {"A": "1"})
        tgt = tmp_env("target.env", {"A": "1", "EXTRA": "only_here"})
        result = sync_env_files(src, tgt)
        assert any(i.conflict == SyncConflict.MISSING_IN_SOURCE for i in result.issues)
        assert "EXTRA" in result.merged

    def test_write_synced_env(self, tmp_env, tmp_path):
        src = tmp_env("source.env", {"A": "1", "B": "2"})
        tgt = tmp_env("target.env", {"A": "1"})
        result = sync_env_files(src, tgt, add_missing=True)
        write_synced_env(result)
        content = result.target_path.read_text()
        assert "B=2" in content

    def test_summary_contains_paths(self, tmp_env):
        src = tmp_env("source.env", {"A": "1"})
        tgt = tmp_env("target.env", {"A": "2"})
        result = sync_env_files(src, tgt)
        summary = result.summary()
        assert "source.env" in summary
        assert "target.env" in summary
