"""Tests for envoy.suffix."""

import os
import tempfile
from pathlib import Path

import pytest

from envoy.suffix import (
    SuffixStatus,
    add_suffix,
    remove_suffix,
    write_suffix_result,
)


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    return p


class TestAddSuffix:
    def test_adds_suffix_to_all_keys(self, env_file):
        result = add_suffix(env_file, "_PROD")
        assert "DB_HOST_PROD" in result.env
        assert "DB_PORT_PROD" in result.env
        assert "APP_NAME_PROD" in result.env

    def test_original_keys_absent_after_add(self, env_file):
        result = add_suffix(env_file, "_PROD")
        assert "DB_HOST" not in result.env

    def test_values_preserved_after_add(self, env_file):
        result = add_suffix(env_file, "_PROD")
        assert result.env["DB_HOST_PROD"] == "localhost"

    def test_add_only_specified_keys(self, env_file):
        result = add_suffix(env_file, "_PROD", keys=["DB_HOST"])
        assert "DB_HOST_PROD" in result.env
        assert "DB_PORT" in result.env  # unchanged
        assert "DB_PORT_PROD" not in result.env

    def test_changed_entries_reported(self, env_file):
        result = add_suffix(env_file, "_X")
        assert all(e.status == SuffixStatus.CHANGED for e in result.changed())
        assert len(result.changed()) == 3

    def test_skipped_entries_when_key_filter_used(self, env_file):
        result = add_suffix(env_file, "_X", keys=["DB_HOST"])
        assert len(result.skipped()) == 2

    def test_summary_string(self, env_file):
        result = add_suffix(env_file, "_X")
        assert "changed" in result.summary()


class TestRemoveSuffix:
    def test_removes_suffix_from_matching_keys(self, env_file):
        # first add, then remove
        added = add_suffix(env_file, "_PROD")
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
            for k, v in added.env.items():
                f.write(f"{k}={v}\n")
            tmp = f.name
        try:
            result = remove_suffix(tmp, "_PROD")
            assert "DB_HOST" in result.env
            assert "DB_HOST_PROD" not in result.env
        finally:
            os.unlink(tmp)

    def test_skips_keys_without_suffix(self, env_file):
        result = remove_suffix(env_file, "_MISSING")
        assert all(e.status == SuffixStatus.SKIPPED for e in result.entries)

    def test_removed_entries_reported(self, env_file):
        added = add_suffix(env_file, "_DEV")
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
            for k, v in added.env.items():
                f.write(f"{k}={v}\n")
            tmp = f.name
        try:
            result = remove_suffix(tmp, "_DEV")
            assert len(result.removed()) == 3
        finally:
            os.unlink(tmp)


class TestWriteSuffixResult:
    def test_writes_new_keys_to_file(self, env_file, tmp_dir):
        result = add_suffix(env_file, "_PROD")
        out = os.path.join(tmp_dir, "out.env")
        write_suffix_result(result, out)
        content = Path(out).read_text()
        assert "DB_HOST_PROD" in content

    def test_written_file_is_parseable(self, env_file, tmp_dir):
        from envoy.parser import parse_env_file

        result = add_suffix(env_file, "_PROD")
        out = os.path.join(tmp_dir, "out.env")
        write_suffix_result(result, out)
        parsed = parse_env_file(out)
        assert parsed["DB_HOST_PROD"] == "localhost"
