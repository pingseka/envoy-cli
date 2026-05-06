"""Tests for envoy.split."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.split import split_env_by_prefix, SplitStatus
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\nAPP_ENV=production\nSECRET_KEY=abc123\n")
    return p


class TestSplitEnvByPrefix:
    def test_creates_file_per_prefix(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_", "APP_"])
        written = [e.output_file for e in result.written()]
        assert any("db_" in w for w in written)
        assert any("app_" in w for w in written)

    def test_written_files_contain_correct_keys(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        split_env_by_prefix(env_file, out, ["DB_"])
        db_file = os.path.join(out, "db_.env")
        parsed = parse_env_file(db_file)
        assert "DB_HOST" in parsed
        assert "DB_PORT" in parsed
        assert "APP_NAME" not in parsed

    def test_strip_prefix_removes_prefix_from_keys(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        split_env_by_prefix(env_file, out, ["DB_"], strip_prefix=True)
        db_file = os.path.join(out, "db_.env")
        parsed = parse_env_file(db_file)
        assert "HOST" in parsed
        assert "PORT" in parsed
        assert "DB_HOST" not in parsed

    def test_unmatched_keys_reported(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_", "APP_"])
        assert "SECRET_KEY" in result.unmatched

    def test_prefix_with_no_match_is_skipped(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["MISSING_"])
        assert all(e.status == SplitStatus.SKIPPED for e in result.entries)

    def test_dry_run_does_not_write_files(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_"], dry_run=True)
        assert result.written()
        assert not os.path.exists(out)

    def test_summary_includes_file_count(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_", "APP_"])
        assert "2 file(s) written" in result.summary()

    def test_summary_mentions_unmatched(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_"])
        assert "unmatched" in result.summary()

    def test_entry_str_contains_filename(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "split")
        result = split_env_by_prefix(env_file, out, ["DB_"])
        entry = result.written()[0]
        assert "db_" in str(entry)
