"""Tests for envoy.rotate."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.rotate import RotateStatus, rotate_keys, apply_rotation


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(tmp_dir):
    p = tmp_dir / ".env"
    _write(p, "DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\n")
    return p


class TestRotateKeys:
    def test_renames_single_key(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        assert result.renamed()[0].new_key == "DATABASE_HOST"
        assert "DATABASE_HOST" in result.env
        assert "DB_HOST" not in result.env

    def test_preserves_value_after_rename(self, env_file):
        result = rotate_keys(env_file, {"DB_PORT": "DATABASE_PORT"})
        assert result.env["DATABASE_PORT"] == "5432"

    def test_not_found_when_key_missing(self, env_file):
        result = rotate_keys(env_file, {"MISSING_KEY": "NEW_KEY"})
        assert len(result.not_found()) == 1
        assert result.not_found()[0].old_key == "MISSING_KEY"

    def test_conflict_when_new_key_exists(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DB_PORT"})
        assert len(result.conflicts()) == 1
        assert result.conflicts()[0].status == RotateStatus.CONFLICT

    def test_ok_false_on_not_found(self, env_file):
        result = rotate_keys(env_file, {"GHOST": "SPIRIT"})
        assert not result.ok()

    def test_ok_true_when_all_renamed(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        assert result.ok()

    def test_bulk_rename_multiple_keys(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
        assert len(result.renamed()) == 2
        assert "DATABASE_HOST" in result.env
        assert "DATABASE_PORT" in result.env

    def test_other_keys_unchanged(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        assert result.env.get("DB_PORT") == "5432"
        assert result.env.get("API_KEY") == "secret"

    def test_summary_reflects_results(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST", "GHOST": "SPIRIT"})
        summary = result.summary()
        assert "renamed" in summary
        assert "not found" in summary

    def test_apply_rotation_writes_file(self, env_file):
        result = rotate_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        apply_rotation(env_file, result)
        content = env_file.read_text()
        assert "DATABASE_HOST" in content
        assert "DB_HOST" not in content
