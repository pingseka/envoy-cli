"""Tests for envoy.promote."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.parser import parse_env_file
from envoy.promote import PromoteStatus, promote_env


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def source_env(tmp_dir):
    p = os.path.join(tmp_dir, "source.env")
    _write(p, "APP_NAME=myapp\nDB_URL=postgres://localhost/dev\nSECRET_KEY=abc123\n")
    return p


@pytest.fixture()
def target_env(tmp_dir):
    p = os.path.join(tmp_dir, "target.env")
    _write(p, "APP_NAME=myapp\nDEBUG=false\n")
    return p


class TestPromoteEnv:
    def test_adds_missing_keys(self, source_env, target_env):
        result = promote_env(source_env, target_env)
        added_keys = {e.key for e in result.added()}
        assert "DB_URL" in added_keys
        assert "SECRET_KEY" in added_keys

    def test_skips_existing_keys_by_default(self, source_env, target_env):
        result = promote_env(source_env, target_env)
        skipped_keys = {e.key for e in result.skipped()}
        assert "APP_NAME" in skipped_keys

    def test_overwrites_when_flag_set(self, source_env, target_env):
        _write(target_env, "APP_NAME=oldname\n")
        result = promote_env(source_env, target_env, overwrite=True)
        updated_keys = {e.key for e in result.updated()}
        assert "APP_NAME" in updated_keys
        env = parse_env_file(target_env)
        assert env["APP_NAME"] == "myapp"

    def test_promotes_only_specified_keys(self, source_env, target_env):
        result = promote_env(source_env, target_env, keys=["DB_URL"])
        added_keys = {e.key for e in result.added()}
        assert "DB_URL" in added_keys
        assert "SECRET_KEY" not in added_keys

    def test_target_file_updated_on_disk(self, source_env, target_env):
        promote_env(source_env, target_env)
        env = parse_env_file(target_env)
        assert "DB_URL" in env
        assert env["DB_URL"] == "postgres://localhost/dev"

    def test_summary_string(self, source_env, target_env):
        result = promote_env(source_env, target_env)
        summary = result.summary()
        assert "added" in summary
        assert "skipped" in summary

    def test_missing_source_raises(self, tmp_dir, target_env):
        with pytest.raises(FileNotFoundError):
            promote_env(os.path.join(tmp_dir, "nonexistent.env"), target_env)

    def test_entry_str_added(self, source_env, target_env):
        result = promote_env(source_env, target_env)
        added = result.added()
        assert added
        assert "added" in str(added[0])

    def test_entry_str_skipped(self, source_env, target_env):
        result = promote_env(source_env, target_env)
        skipped = result.skipped()
        assert skipped
        assert "skipped" in str(skipped[0])

    def test_entry_str_updated(self, source_env, target_env):
        _write(target_env, "APP_NAME=old\n")
        result = promote_env(source_env, target_env, overwrite=True)
        updated = result.updated()
        assert updated
        assert "updated" in str(updated[0])
