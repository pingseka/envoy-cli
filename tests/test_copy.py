"""Tests for envoy.copy module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envoy.copy import CopyStatus, copy_keys
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def source_env(tmp_dir):
    p = os.path.join(tmp_dir, "source.env")
    _write(p, "FOO=hello\nBAR=world\nSECRET_KEY=abc123\n")
    return p


@pytest.fixture()
def target_env(tmp_dir):
    p = os.path.join(tmp_dir, "target.env")
    _write(p, "BAZ=existing\nBAR=old_value\n")
    return p


class TestCopyKeys:
    def test_copies_missing_key(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["FOO"])
        assert len(result.copied) == 1
        assert result.copied[0].key == "FOO"
        data = parse_env_file(target_env)
        assert data["FOO"] == "hello"

    def test_skips_existing_key_without_overwrite(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["BAR"], overwrite=False)
        assert len(result.skipped) == 1
        data = parse_env_file(target_env)
        assert data["BAR"] == "old_value"

    def test_overwrites_existing_key_when_flag_set(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["BAR"], overwrite=True)
        assert len(result.copied) == 1
        data = parse_env_file(target_env)
        assert data["BAR"] == "world"

    def test_not_found_for_missing_source_key(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["NOPE"])
        assert len(result.not_found) == 1
        assert result.not_found[0].key == "NOPE"

    def test_mixed_statuses(self, source_env, target_env):
        result = copy_keys(
            source_env, target_env, keys=["FOO", "BAR", "NOPE"], overwrite=False
        )
        assert len(result.copied) == 1
        assert len(result.skipped) == 1
        assert len(result.not_found) == 1

    def test_summary_string(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["FOO", "BAR", "NOPE"])
        summary = result.summary()
        assert "copied" in summary
        assert "skipped" in summary
        assert "not found" in summary

    def test_existing_keys_preserved(self, source_env, target_env):
        copy_keys(source_env, target_env, keys=["FOO"])
        data = parse_env_file(target_env)
        assert data["BAZ"] == "existing"

    def test_entry_str_copied(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["FOO"])
        assert "copied" in str(result.copied[0]).lower()

    def test_entry_str_skipped(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["BAR"], overwrite=False)
        assert "skipped" in str(result.skipped[0]).lower()

    def test_entry_str_not_found(self, source_env, target_env):
        result = copy_keys(source_env, target_env, keys=["GHOST"])
        assert "missing" in str(result.not_found[0]).lower()
