"""Tests for envoy.strip."""

from __future__ import annotations

import os
import tempfile

import pytest

from envoy.strip import StripStatus, strip_keys


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "APP_NAME=myapp\nDEBUG=true\nSECRET_KEY=abc123\nDB_URL=postgres://localhost/db\n")
    return p


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestStripKeys:
    def test_removes_exact_key(self, env_file):
        result = strip_keys(env_file, ["DEBUG"])
        assert "DEBUG" not in result.output
        assert "APP_NAME" in result.output

    def test_removed_entry_has_correct_status(self, env_file):
        result = strip_keys(env_file, ["DEBUG"])
        removed = result.removed()
        assert len(removed) == 1
        assert removed[0].key == "DEBUG"
        assert removed[0].status == StripStatus.REMOVED

    def test_skipped_when_key_not_found(self, env_file):
        result = strip_keys(env_file, ["NONEXISTENT"])
        skipped = result.skipped()
        assert len(skipped) == 1
        assert skipped[0].key == "NONEXISTENT"
        assert skipped[0].status == StripStatus.SKIPPED

    def test_wildcard_removes_multiple_keys(self, env_file):
        result = strip_keys(env_file, ["SECRET_*"])
        assert "SECRET_KEY" not in result.output
        assert len(result.removed()) == 1

    def test_wildcard_prefix_removes_db_keys(self, env_file):
        result = strip_keys(env_file, ["DB_*"])
        assert "DB_URL" not in result.output
        assert "APP_NAME" in result.output

    def test_dry_run_does_not_modify_file(self, env_file):
        original = open(env_file).read()
        strip_keys(env_file, ["DEBUG"], dry_run=True)
        assert open(env_file).read() == original

    def test_writes_to_output_path(self, env_file, tmp_dir):
        out = os.path.join(tmp_dir, "out.env")
        strip_keys(env_file, ["DEBUG"], output_path=out)
        assert os.path.exists(out)
        content = open(out).read()
        assert "DEBUG" not in content
        assert "APP_NAME" in content

    def test_original_file_unchanged_when_output_path_given(self, env_file, tmp_dir):
        original = open(env_file).read()
        out = os.path.join(tmp_dir, "out.env")
        strip_keys(env_file, ["DEBUG"], output_path=out)
        assert open(env_file).read() == original

    def test_summary_counts(self, env_file):
        result = strip_keys(env_file, ["DEBUG", "MISSING"])
        assert "1 key(s) removed" in result.summary()
        assert "1 key(s) not found" in result.summary()

    def test_str_entry_removed(self, env_file):
        result = strip_keys(env_file, ["DEBUG"])
        assert str(result.removed()[0]).startswith("-")

    def test_str_entry_skipped(self, env_file):
        result = strip_keys(env_file, ["GHOST"])
        assert str(result.skipped()[0]).startswith("~")
