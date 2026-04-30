"""Tests for envoy.freeze module."""
from __future__ import annotations

import pytest
from pathlib import Path

from envoy.freeze import FreezeStatus, freeze_env, check_frozen


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "DB_HOST=localhost\nDB_PASS=secret\nAPP_ENV=production\n",
    )


class TestFreezeEnv:
    def test_locks_all_keys_by_default(self, env_file: Path) -> None:
        result = freeze_env(env_file)
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["DB_HOST"] == FreezeStatus.LOCKED
        assert statuses["DB_PASS"] == FreezeStatus.LOCKED
        assert statuses["APP_ENV"] == FreezeStatus.LOCKED

    def test_locks_only_specified_keys(self, env_file: Path) -> None:
        result = freeze_env(env_file, keys=["DB_HOST"])
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["DB_HOST"] == FreezeStatus.LOCKED
        assert len(result.entries) == 1

    def test_skips_missing_key(self, env_file: Path) -> None:
        result = freeze_env(env_file, keys=["NONEXISTENT"])
        assert result.entries[0].status == FreezeStatus.SKIPPED

    def test_already_locked_on_second_call(self, env_file: Path) -> None:
        freeze_env(env_file, keys=["DB_HOST"])
        result = freeze_env(env_file, keys=["DB_HOST"])
        statuses = {e.key: e.status for e in result.entries}
        assert statuses["DB_HOST"] == FreezeStatus.ALREADY_LOCKED

    def test_lockfile_created_at_default_path(self, env_file: Path) -> None:
        result = freeze_env(env_file)
        assert result.lockfile is not None
        assert result.lockfile.exists()
        assert result.lockfile.suffix == ".lock"

    def test_lockfile_created_at_custom_path(self, env_file: Path, tmp_dir: Path) -> None:
        custom = tmp_dir / "custom.lock"
        result = freeze_env(env_file, lockfile_path=custom)
        assert result.lockfile == custom
        assert custom.exists()

    def test_summary_string(self, env_file: Path) -> None:
        result = freeze_env(env_file)
        summary = result.summary()
        assert "locked" in summary

    def test_locked_helper(self, env_file: Path) -> None:
        result = freeze_env(env_file)
        assert len(result.locked()) == 3

    def test_skipped_helper(self, env_file: Path) -> None:
        result = freeze_env(env_file, keys=["MISSING_KEY"])
        assert len(result.skipped()) == 1


class TestCheckFrozen:
    def test_returns_empty_when_no_lockfile(self, env_file: Path) -> None:
        result = check_frozen(env_file)
        assert result == {}

    def test_all_true_when_values_unchanged(self, env_file: Path) -> None:
        freeze_env(env_file)
        result = check_frozen(env_file)
        assert all(result.values())

    def test_detects_changed_value(self, env_file: Path) -> None:
        freeze_env(env_file, keys=["DB_HOST"])
        env_file.write_text("DB_HOST=changed\nDB_PASS=secret\nAPP_ENV=production\n")
        result = check_frozen(env_file)
        assert result["DB_HOST"] is False

    def test_custom_lockfile_path(self, env_file: Path, tmp_dir: Path) -> None:
        custom = tmp_dir / "my.lock"
        freeze_env(env_file, keys=["APP_ENV"], lockfile_path=custom)
        result = check_frozen(env_file, lockfile_path=custom)
        assert "APP_ENV" in result
        assert result["APP_ENV"] is True
