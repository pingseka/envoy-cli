"""Tests for envoy.dedup."""
from __future__ import annotations

import os
import tempfile

import pytest

from envoy.dedup import DedupStatus, dedup_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(
        p,
        "APP_KEY=secret\n"
        "DB_PASS=secret\n"
        "API_TOKEN=token123\n"
        "BACKUP_TOKEN=token123\n"
        "UNIQUE=only_one\n",
    )
    return p


class TestDedupEnv:
    def test_detects_duplicate_values(self, env_file):
        result = dedup_env(env_file)
        removed_keys = {e.key for e in result.removed}
        # One of the pair should be removed
        assert len(removed_keys) == 2
        assert "DB_PASS" in removed_keys or "APP_KEY" in removed_keys
        assert "BACKUP_TOKEN" in removed_keys or "API_TOKEN" in removed_keys

    def test_keep_first_retains_first_occurrence(self, env_file):
        result = dedup_env(env_file, keep="first")
        kept_keys = {e.key for e in result.kept}
        assert "APP_KEY" in kept_keys  # first of 'secret'
        assert "API_TOKEN" in kept_keys  # first of 'token123'

    def test_keep_last_retains_last_occurrence(self, env_file):
        result = dedup_env(env_file, keep="last")
        kept_keys = {e.key for e in result.kept}
        assert "DB_PASS" in kept_keys  # last of 'secret'
        assert "BACKUP_TOKEN" in kept_keys  # last of 'token123'

    def test_unique_keys_always_kept(self, env_file):
        result = dedup_env(env_file)
        kept_keys = {e.key for e in result.kept}
        assert "UNIQUE" in kept_keys

    def test_removed_entry_has_duplicate_of_set(self, env_file):
        result = dedup_env(env_file, keep="first")
        removed = {e.key: e for e in result.removed}
        assert removed["DB_PASS"].duplicate_of == "APP_KEY"
        assert removed["BACKUP_TOKEN"].duplicate_of == "API_TOKEN"

    def test_result_env_excludes_removed_keys(self, env_file):
        result = dedup_env(env_file)
        for entry in result.removed:
            assert entry.key not in result.env

    def test_no_duplicates_returns_all_kept(self, tmp_dir):
        p = os.path.join(tmp_dir, "unique.env")
        _write(p, "A=1\nB=2\nC=3\n")
        result = dedup_env(p)
        assert result.removed_count == 0
        assert len(result.kept) == 3

    def test_summary_string(self, env_file):
        result = dedup_env(env_file)
        s = result.summary()
        assert "kept" in s
        assert "removed" in s

    def test_str_removed_entry_mentions_duplicate_of(self, env_file):
        result = dedup_env(env_file, keep="first")
        removed = {e.key: e for e in result.removed}
        s = str(removed["DB_PASS"])
        assert "duplicate of" in s
        assert "APP_KEY" in s

    def test_str_kept_entry_shows_value(self, tmp_dir):
        p = os.path.join(tmp_dir, "k.env")
        _write(p, "FOO=bar\n")
        result = dedup_env(p)
        assert "FOO=bar" in str(result.kept[0])
