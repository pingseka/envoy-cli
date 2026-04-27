"""Tests for envoy.mask module."""

from __future__ import annotations

import os
import tempfile

import pytest

from envoy.mask import MaskStatus, mask_env, MASK_PLACEHOLDER


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    path = os.path.join(tmp_dir, ".env")
    _write(path, "APP_NAME=myapp\nSECRET_KEY=supersecret\nDEBUG=true\nDB_PASSWORD=hunter2\n")
    return path


class TestMaskEnv:
    def test_masks_explicit_key(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY"])
        assert result.masked_env["SECRET_KEY"] == MASK_PLACEHOLDER
        assert result.masked_env["APP_NAME"] == "myapp"

    def test_masked_count(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY", "DB_PASSWORD"])
        assert result.masked_count == 2

    def test_skipped_count(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY"])
        assert result.skipped_count == 3  # APP_NAME, DEBUG, DB_PASSWORD

    def test_missing_key_status(self, env_file):
        result = mask_env(env_file, keys=["NONEXISTENT"])
        entry = next(e for e in result.entries if e.key == "NONEXISTENT")
        assert entry.status == MaskStatus.NOT_FOUND

    def test_pattern_masks_matching_keys(self, env_file):
        result = mask_env(env_file, pattern=r"PASSWORD")
        assert result.masked_env["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert result.masked_env["APP_NAME"] == "myapp"

    def test_auto_secrets_masks_secret_keys(self, env_file):
        result = mask_env(env_file, auto_secrets=True)
        # SECRET_KEY and DB_PASSWORD should be masked
        assert result.masked_env["SECRET_KEY"] == MASK_PLACEHOLDER
        assert result.masked_env["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert result.masked_env["APP_NAME"] == "myapp"

    def test_original_value_stored_in_entry(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY"])
        entry = next(e for e in result.entries if e.key == "SECRET_KEY")
        assert entry.original == "supersecret"

    def test_deduplicates_keys(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY", "SECRET_KEY"])
        masked_entries = [e for e in result.entries if e.status == MaskStatus.MASKED]
        assert sum(1 for e in masked_entries if e.key == "SECRET_KEY") == 1

    def test_file_not_found_raises(self, tmp_dir):
        with pytest.raises(FileNotFoundError):
            mask_env(os.path.join(tmp_dir, "missing.env"), keys=["KEY"])

    def test_summary_string(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY", "DB_PASSWORD"])
        assert "2 masked" in result.summary()

    def test_entry_str_masked(self, env_file):
        result = mask_env(env_file, keys=["SECRET_KEY"])
        entry = next(e for e in result.entries if e.key == "SECRET_KEY")
        assert "masked" in str(entry)

    def test_entry_str_not_found(self, env_file):
        result = mask_env(env_file, keys=["MISSING"])
        entry = next(e for e in result.entries if e.key == "MISSING")
        assert "missing" in str(entry)
