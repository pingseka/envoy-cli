"""Tests for envoy.sort and envoy.cli_sort."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

from envoy.sort import SortOrder, SortResult, sort_env
from envoy.cli_sort import cmd_sort


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def env_file(tmp_dir: Path) -> Path:
    p = tmp_dir / ".env"
    _write(p, "ZEBRA=1\nAPPLE=2\nMANGO=3\n")
    return p


class TestSortEnv:
    def test_asc_order(self, env_file: Path) -> None:
        result = sort_env(env_file, order=SortOrder.ASC)
        assert result.sorted_order == ["APPLE", "MANGO", "ZEBRA"]

    def test_desc_order(self, env_file: Path) -> None:
        result = sort_env(env_file, order=SortOrder.DESC)
        assert result.sorted_order == ["ZEBRA", "MANGO", "APPLE"]

    def test_already_sorted_not_changed(self, tmp_dir: Path) -> None:
        p = tmp_dir / ".env"
        _write(p, "ALPHA=1\nBETA=2\nGAMMA=3\n")
        result = sort_env(p, order=SortOrder.ASC)
        assert not result.changed

    def test_write_updates_file(self, env_file: Path) -> None:
        sort_env(env_file, order=SortOrder.ASC, write=True)
        content = env_file.read_text()
        keys = [line.split("=")[0] for line in content.splitlines() if "=" in line]
        assert keys == ["APPLE", "MANGO", "ZEBRA"]

    def test_dry_run_does_not_write(self, env_file: Path) -> None:
        original = env_file.read_text()
        sort_env(env_file, order=SortOrder.ASC, write=False)
        assert env_file.read_text() == original

    def test_group_prefixes(self, tmp_dir: Path) -> None:
        p = tmp_dir / ".env"
        _write(p, "DB_PORT=5432\nAWS_KEY=abc\nDB_HOST=localhost\nAWS_SECRET=xyz\n")
        result = sort_env(p, order=SortOrder.ASC, group_prefixes=True)
        # AWS group comes before DB group
        aws_idx = result.sorted_order.index("AWS_KEY")
        db_idx = result.sorted_order.index("DB_HOST")
        assert aws_idx < db_idx

    def test_summary_when_changed(self, env_file: Path) -> None:
        result = sort_env(env_file, order=SortOrder.ASC)
        assert "Sorted" in result.summary()

    def test_summary_when_no_change(self, tmp_dir: Path) -> None:
        p = tmp_dir / ".env"
        _write(p, "A=1\nB=2\n")
        result = sort_env(p, order=SortOrder.ASC)
        assert "Already sorted" in result.summary()


def make_args(**kwargs) -> Namespace:  # type: ignore[return]
    defaults = {
        "file": "",
        "order": "asc",
        "dry_run": False,
        "group_prefixes": False,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestCmdSort:
    def test_exits_zero_on_success(self, env_file: Path) -> None:
        args = make_args(file=str(env_file))
        assert cmd_sort(args) == 0

    def test_exits_one_for_missing_file(self, tmp_dir: Path) -> None:
        args = make_args(file=str(tmp_dir / "missing.env"))
        assert cmd_sort(args) == 1

    def test_exits_one_for_invalid_order(self, env_file: Path) -> None:
        args = make_args(file=str(env_file), order="sideways")
        assert cmd_sort(args) == 1

    def test_dry_run_does_not_modify_file(self, env_file: Path) -> None:
        original = env_file.read_text()
        args = make_args(file=str(env_file), dry_run=True)
        cmd_sort(args)
        assert env_file.read_text() == original
