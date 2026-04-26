"""Tests for envoy.rename module."""

import os
import tempfile
import pytest
from envoy.rename import rename_keys, RenameEntry, RenameResult


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    path = os.path.join(tmp_dir, ".env")
    _write(path, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    return path


class TestRenameKeys:
    def test_renames_existing_key(self, env_file):
        result = rename_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        assert result.renamed == 1
        assert result.skipped == 0

    def test_renamed_key_appears_in_file(self, env_file):
        rename_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        from envoy.parser import parse_env_file
        data = parse_env_file(env_file)
        assert "DATABASE_HOST" in data
        assert "DB_HOST" not in data
        assert data["DATABASE_HOST"] == "localhost"

    def test_skips_missing_key(self, env_file):
        result = rename_keys(env_file, {"MISSING_KEY": "NEW_KEY"})
        assert result.renamed == 0
        assert result.skipped == 1
        assert result.entries[0].skip_reason == "key not found"

    def test_skips_when_target_exists_without_overwrite(self, env_file):
        result = rename_keys(env_file, {"DB_HOST": "DB_PORT"})
        assert result.skipped == 1
        assert "already exists" in result.entries[0].skip_reason

    def test_allows_overwrite_when_flag_set(self, env_file):
        result = rename_keys(env_file, {"DB_HOST": "DB_PORT"}, overwrite=True)
        assert result.renamed == 1

    def test_dry_run_does_not_write(self, env_file):
        rename_keys(env_file, {"DB_HOST": "DATABASE_HOST"}, dry_run=True)
        from envoy.parser import parse_env_file
        data = parse_env_file(env_file)
        assert "DB_HOST" in data
        assert "DATABASE_HOST" not in data

    def test_multiple_renames(self, env_file):
        result = rename_keys(
            env_file,
            {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"},
        )
        assert result.renamed == 2
        assert result.skipped == 0

    def test_summary_string(self, env_file):
        result = rename_keys(env_file, {"DB_HOST": "DATABASE_HOST", "MISSING": "X"})
        assert "1 renamed" in result.summary()
        assert "1 skipped" in result.summary()

    def test_has_renames_true(self, env_file):
        result = rename_keys(env_file, {"DB_HOST": "DATABASE_HOST"})
        assert result.has_renames() is True

    def test_has_renames_false_when_all_skipped(self, env_file):
        result = rename_keys(env_file, {"NOPE": "ALSO_NOPE"})
        assert result.has_renames() is False


class TestRenameEntry:
    def test_str_renamed(self):
        e = RenameEntry(old_key="A", new_key="B", value="v")
        assert "RENAME" in str(e)
        assert "A" in str(e)
        assert "B" in str(e)

    def test_str_skipped(self):
        e = RenameEntry(old_key="A", new_key="B", value="", skipped=True, skip_reason="key not found")
        assert "SKIP" in str(e)
        assert "key not found" in str(e)
