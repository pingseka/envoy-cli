"""Tests for envoy.patch."""

from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest

from envoy.patch import PatchOp, patch_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture()
def tmp_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture()
def env_file(tmp_dir: str) -> str:
    path = os.path.join(tmp_dir, ".env")
    _write(path, "FOO=bar\nBAZ=qux\nSECRET_KEY=abc123\n")
    return path


class TestPatchEnv:
    def test_updates_existing_key(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": "updated"})
        assert result.env["FOO"] == "updated"

    def test_adds_new_key(self, env_file: str) -> None:
        result = patch_env(env_file, {"NEW_KEY": "hello"})
        assert result.env["NEW_KEY"] == "hello"

    def test_deletes_key_with_none(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": None})
        assert "FOO" not in result.env

    def test_delete_nonexistent_key_is_silent(self, env_file: str) -> None:
        result = patch_env(env_file, {"DOES_NOT_EXIST": None})
        assert len(result.deleted) == 0

    def test_unchanged_keys_preserved(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": "new"})
        assert result.env["BAZ"] == "qux"

    def test_entry_op_set_for_update(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": "new"})
        entry = next(e for e in result.entries if e.key == "FOO")
        assert entry.op == PatchOp.SET
        assert entry.old_value == "bar"
        assert entry.new_value == "new"

    def test_entry_op_delete(self, env_file: str) -> None:
        result = patch_env(env_file, {"BAZ": None})
        entry = next(e for e in result.entries if e.key == "BAZ")
        assert entry.op == PatchOp.DELETE
        assert entry.old_value == "qux"

    def test_added_property(self, env_file: str) -> None:
        result = patch_env(env_file, {"BRAND_NEW": "yes"})
        assert len(result.added) == 1
        assert result.added[0].key == "BRAND_NEW"

    def test_changed_property(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": "changed"})
        assert len(result.changed) == 1

    def test_summary_string(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": "x", "EXTRA": "y", "BAZ": None})
        summary = result.summary()
        assert "added" in summary
        assert "updated" in summary
        assert "deleted" in summary

    def test_str_entry_set_new(self, env_file: str) -> None:
        result = patch_env(env_file, {"FRESH": "val"})
        entry = result.added[0]
        assert "[+]" in str(entry)

    def test_str_entry_delete(self, env_file: str) -> None:
        result = patch_env(env_file, {"FOO": None})
        assert "[-]" in str(result.deleted[0])

    def test_file_not_found_raises(self, tmp_dir: str) -> None:
        with pytest.raises(FileNotFoundError):
            patch_env(os.path.join(tmp_dir, "missing.env"), {"A": "1"})
