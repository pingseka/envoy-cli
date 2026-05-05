"""Tests for envoy.reorder."""
from __future__ import annotations

import pytest
from pathlib import Path

from envoy.reorder import ReorderStatus, reorder_env


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "ALPHA=1\nBETA=2\nGAMMA=3\nDELTA=4\n",
    )


class TestReorderEnv:
    def test_reorders_keys_to_specified_order(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["DELTA", "GAMMA", "BETA", "ALPHA"])
        keys = list(result.env.keys())
        assert keys == ["DELTA", "GAMMA", "BETA", "ALPHA"]

    def test_values_preserved_after_reorder(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["GAMMA", "ALPHA"])
        assert result.env["GAMMA"] == "3"
        assert result.env["ALPHA"] == "1"

    def test_unspecified_keys_appended_by_default(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["GAMMA"])
        keys = list(result.env.keys())
        assert keys[0] == "GAMMA"
        assert "ALPHA" in keys
        assert "BETA" in keys
        assert "DELTA" in keys

    def test_drop_removes_unspecified_keys(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["ALPHA", "GAMMA"], append_unspecified=False)
        assert list(result.env.keys()) == ["ALPHA", "GAMMA"]
        assert "BETA" not in result.env
        assert "DELTA" not in result.env

    def test_moved_entries_have_correct_status(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["DELTA", "ALPHA", "BETA", "GAMMA"])
        moved = result.moved()
        moved_keys = [e.key for e in moved]
        assert "DELTA" in moved_keys

    def test_unchanged_entry_when_position_same(self, env_file: Path) -> None:
        # ALPHA is first in file and first in order list
        result = reorder_env(env_file, ["ALPHA", "BETA", "GAMMA", "DELTA"])
        unchanged = [e for e in result.entries if e.status == ReorderStatus.UNCHANGED]
        unchanged_keys = [e.key for e in unchanged]
        assert "ALPHA" in unchanged_keys

    def test_unspecified_entries_reported(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["ALPHA"])
        unspecified = result.unspecified()
        unspecified_keys = [e.key for e in unspecified]
        assert "BETA" in unspecified_keys
        assert "GAMMA" in unspecified_keys
        assert "DELTA" in unspecified_keys

    def test_summary_string(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["DELTA", "GAMMA", "BETA", "ALPHA"])
        s = result.summary()
        assert "moved" in s

    def test_partial_order_preserves_all_values(self, env_file: Path) -> None:
        result = reorder_env(env_file, ["BETA"])
        assert len(result.env) == 4
        for v in ["1", "2", "3", "4"]:
            assert v in result.env.values()

    def test_empty_order_appends_all_as_unspecified(self, env_file: Path) -> None:
        result = reorder_env(env_file, [])
        assert len(result.env) == 4
        assert all(e.status == ReorderStatus.UNSPECIFIED for e in result.entries)
