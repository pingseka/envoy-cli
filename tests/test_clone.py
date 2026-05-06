"""Tests for envoy.clone module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.clone import CloneStatus, clone_env
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def source_env(tmp_dir):
    p = os.path.join(tmp_dir, "source.env")
    _write(p, "APP_HOST=localhost\nAPP_PORT=8080\nDB_URL=postgres://localhost/db\n")
    return p


@pytest.fixture()
def dest_env(tmp_dir):
    return os.path.join(tmp_dir, "dest.env")


class TestCloneEnv:
    def test_copies_all_keys_by_default(self, source_env, dest_env):
        result = clone_env(source_env, dest_env)
        parsed = parse_env_file(dest_env)
        assert parsed["APP_HOST"] == "localhost"
        assert parsed["APP_PORT"] == "8080"
        assert parsed["DB_URL"] == "postgres://localhost/db"

    def test_all_entries_copied_status(self, source_env, dest_env):
        result = clone_env(source_env, dest_env)
        statuses = {e.status for e in result.entries}
        assert statuses == {CloneStatus.COPIED}

    def test_prefix_filter_excludes_non_matching(self, source_env, dest_env):
        result = clone_env(source_env, dest_env, prefix_filter="APP_")
        parsed = parse_env_file(dest_env)
        assert "APP_HOST" in parsed
        assert "APP_PORT" in parsed
        assert "DB_URL" not in parsed

    def test_skipped_entries_recorded(self, source_env, dest_env):
        result = clone_env(source_env, dest_env, prefix_filter="APP_")
        skipped = result.skipped()
        assert any(e.source_key == "DB_URL" for e in skipped)

    def test_strip_prefix_removes_prefix_from_dest_keys(self, source_env, dest_env):
        result = clone_env(source_env, dest_env, prefix_filter="APP_", strip_prefix=True)
        parsed = parse_env_file(dest_env)
        assert "HOST" in parsed
        assert "PORT" in parsed
        assert "APP_HOST" not in parsed

    def test_strip_prefix_sets_renamed_status(self, source_env, dest_env):
        result = clone_env(source_env, dest_env, prefix_filter="APP_", strip_prefix=True)
        assert len(result.renamed()) == 2

    def test_key_map_renames_specific_key(self, source_env, dest_env):
        result = clone_env(source_env, dest_env, key_map={"APP_HOST": "HOST_NAME"})
        parsed = parse_env_file(dest_env)
        assert "HOST_NAME" in parsed
        assert parsed["HOST_NAME"] == "localhost"

    def test_summary_string_contains_destination(self, source_env, dest_env):
        result = clone_env(source_env, dest_env)
        assert dest_env in result.summary()

    def test_missing_source_raises(self, dest_env):
        with pytest.raises(FileNotFoundError):
            clone_env("/nonexistent/.env", dest_env)
