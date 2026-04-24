"""Tests for envoy.merge module."""

import os
import tempfile
import pytest

from envoy.merge import (
    merge_env_files,
    write_merged,
    MergeStrategy,
    MergeConflict,
    MergeResult,
)


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def base_env(tmp_dir):
    p = os.path.join(tmp_dir, "base.env")
    _write(p, "APP_NAME=myapp\nDB_HOST=localhost\nSECRET_KEY=abc123\n")
    return p


@pytest.fixture
def incoming_env(tmp_dir):
    p = os.path.join(tmp_dir, "incoming.env")
    _write(p, "APP_NAME=myapp\nDB_HOST=remotehost\nNEW_VAR=hello\n")
    return p


class TestMergeEnvFiles:
    def test_union_strategy_keeps_all_keys(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        assert "APP_NAME" in result.merged
        assert "DB_HOST" in result.merged
        assert "SECRET_KEY" in result.merged
        assert "NEW_VAR" in result.merged

    def test_detects_conflict(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        assert result.has_conflicts
        keys = [c.key for c in result.conflicts]
        assert "DB_HOST" in keys

    def test_no_conflict_for_equal_values(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        keys = [c.key for c in result.conflicts]
        assert "APP_NAME" not in keys

    def test_ours_strategy_prefers_base_on_conflict(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.OURS)
        assert result.merged["DB_HOST"] == "localhost"

    def test_theirs_strategy_prefers_incoming_on_conflict(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.THEIRS)
        assert result.merged["DB_HOST"] == "remotehost"

    def test_added_keys_tracked(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        assert "NEW_VAR" in result.added

    def test_theirs_removes_base_only_keys(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.THEIRS)
        assert "SECRET_KEY" in result.removed
        assert "SECRET_KEY" not in result.merged

    def test_union_keeps_base_only_keys(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        assert "SECRET_KEY" not in result.removed
        assert result.merged["SECRET_KEY"] == "abc123"

    def test_summary_no_changes(self, tmp_dir):
        p1 = os.path.join(tmp_dir, "a.env")
        p2 = os.path.join(tmp_dir, "b.env")
        _write(p1, "FOO=bar\n")
        _write(p2, "FOO=bar\n")
        result = merge_env_files(p1, p2)
        assert result.summary() == "no changes"

    def test_summary_with_changes(self, base_env, incoming_env):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.UNION)
        summary = result.summary()
        assert "added" in summary
        assert "conflict" in summary

    def test_write_merged_creates_file(self, base_env, incoming_env, tmp_dir):
        result = merge_env_files(base_env, incoming_env, MergeStrategy.OURS)
        out = os.path.join(tmp_dir, "merged.env")
        write_merged(result, out)
        assert os.path.exists(out)
        with open(out) as f:
            content = f.read()
        assert "APP_NAME" in content
