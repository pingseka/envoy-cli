"""Tests for envoy.cli_rotate."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy.cli_rotate import cmd_rotate


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    _write(p, "OLD_KEY=hello\nOTHER=world\n")
    return p


def make_args(file, map_pairs=None, dry_run=False):
    ns = argparse.Namespace()
    ns.file = str(file)
    ns.map = map_pairs
    ns.dry_run = dry_run
    return ns


class TestCmdRotate:
    def test_exits_zero_on_success(self, tmp_env):
        args = make_args(tmp_env, map_pairs=["OLD_KEY=NEW_KEY"])
        assert cmd_rotate(args) == 0

    def test_file_updated_after_rotate(self, tmp_env):
        args = make_args(tmp_env, map_pairs=["OLD_KEY=NEW_KEY"])
        cmd_rotate(args)
        content = tmp_env.read_text()
        assert "NEW_KEY" in content
        assert "OLD_KEY" not in content

    def test_dry_run_does_not_write(self, tmp_env):
        original = tmp_env.read_text()
        args = make_args(tmp_env, map_pairs=["OLD_KEY=NEW_KEY"], dry_run=True)
        cmd_rotate(args)
        assert tmp_env.read_text() == original

    def test_exits_one_when_file_missing(self, tmp_path):
        args = make_args(tmp_path / "ghost.env", map_pairs=["A=B"])
        assert cmd_rotate(args) == 1

    def test_exits_one_when_no_map(self, tmp_env):
        args = make_args(tmp_env, map_pairs=None)
        assert cmd_rotate(args) == 1

    def test_exits_one_on_invalid_map_format(self, tmp_env):
        args = make_args(tmp_env, map_pairs=["BADFORMAT"])
        assert cmd_rotate(args) == 1

    def test_exits_one_on_not_found(self, tmp_env):
        args = make_args(tmp_env, map_pairs=["MISSING=NEW"])
        assert cmd_rotate(args) == 1

    def test_exits_one_on_conflict(self, tmp_env):
        args = make_args(tmp_env, map_pairs=["OLD_KEY=OTHER"])
        assert cmd_rotate(args) == 1
