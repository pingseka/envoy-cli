"""Tests for envoy.compare module."""
import os
import tempfile
import pytest

from envoy.compare import (
    compare_env_files, ChangeType, CompareEntry, CompareResult
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
    _write(p, "APP_NAME=envoy\nDB_HOST=localhost\nSECRET_KEY=abc123\n")
    return p


@pytest.fixture
def target_env(tmp_dir):
    p = os.path.join(tmp_dir, "target.env")
    _write(p, "APP_NAME=envoy\nDB_HOST=remotehost\nNEW_VAR=hello\n")
    return p


class TestCompareEnvFiles:
    def test_detects_added_key(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        keys = {e.key for e in result.added}
        assert "NEW_VAR" in keys

    def test_detects_removed_key(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        keys = {e.key for e in result.removed}
        assert "SECRET_KEY" in keys

    def test_detects_modified_key(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        keys = {e.key for e in result.modified}
        assert "DB_HOST" in keys

    def test_unchanged_excluded_by_default(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        assert result.unchanged == []

    def test_unchanged_included_when_requested(self, base_env, target_env):
        result = compare_env_files(base_env, target_env, include_unchanged=True)
        keys = {e.key for e in result.unchanged}
        assert "APP_NAME" in keys

    def test_has_changes_true_when_diffs_exist(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        assert result.has_changes is True

    def test_has_changes_false_for_identical_files(self, tmp_dir):
        p = os.path.join(tmp_dir, "same.env")
        _write(p, "FOO=bar\n")
        result = compare_env_files(p, p)
        assert result.has_changes is False

    def test_summary_string(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        s = result.summary()
        assert "+" in s and "-" in s and "~" in s

    def test_secret_key_masked_in_display(self, tmp_dir):
        b = os.path.join(tmp_dir, "b.env")
        t = os.path.join(tmp_dir, "t.env")
        _write(b, "SECRET_KEY=old\n")
        _write(t, "SECRET_KEY=new\n")
        result = compare_env_files(b, t)
        entry = result.modified[0]
        assert entry.display_base() == "***"
        assert entry.display_target() == "***"

    def test_entry_str_contains_symbol(self, base_env, target_env):
        result = compare_env_files(base_env, target_env)
        added = result.added[0]
        assert str(added).startswith("+")

    def test_empty_files_produce_no_entries(self, tmp_dir):
        b = os.path.join(tmp_dir, "empty_b.env")
        t = os.path.join(tmp_dir, "empty_t.env")
        _write(b, "")
        _write(t, "")
        result = compare_env_files(b, t)
        assert result.entries == []
