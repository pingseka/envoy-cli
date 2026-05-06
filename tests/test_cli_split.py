"""Tests for envoy.cli_split."""

from __future__ import annotations

import os
import tempfile
import types
from pathlib import Path

import pytest

from envoy.cli_split import cmd_split


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture
def tmp_env():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, ".env")
        _write(p, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
        yield p, d


def make_args(**kwargs):
    defaults = {
        "file": "",
        "output_dir": "",
        "prefixes": [],
        "strip_prefix": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestCmdSplit:
    def test_exits_zero_on_success(self, tmp_env):
        env_file, tmp_dir = tmp_env
        out = os.path.join(tmp_dir, "split")
        args = make_args(file=env_file, output_dir=out, prefixes=["DB_"])
        assert cmd_split(args) == 0

    def test_exits_two_when_no_prefixes(self, tmp_env):
        env_file, tmp_dir = tmp_env
        args = make_args(file=env_file, output_dir=tmp_dir, prefixes=[])
        assert cmd_split(args) == 2

    def test_exits_one_on_missing_file(self, tmp_env):
        _, tmp_dir = tmp_env
        args = make_args(file="/nonexistent/.env", output_dir=tmp_dir, prefixes=["DB_"])
        assert cmd_split(args) == 1

    def test_dry_run_exits_zero(self, tmp_env):
        env_file, tmp_dir = tmp_env
        out = os.path.join(tmp_dir, "split")
        args = make_args(file=env_file, output_dir=out, prefixes=["DB_"], dry_run=True)
        assert cmd_split(args) == 0

    def test_dry_run_does_not_create_dir(self, tmp_env):
        env_file, tmp_dir = tmp_env
        out = os.path.join(tmp_dir, "split_dry")
        args = make_args(file=env_file, output_dir=out, prefixes=["DB_"], dry_run=True)
        cmd_split(args)
        assert not os.path.exists(out)

    def test_output_file_created_for_prefix(self, tmp_env):
        env_file, tmp_dir = tmp_env
        out = os.path.join(tmp_dir, "split")
        args = make_args(file=env_file, output_dir=out, prefixes=["APP_"])
        cmd_split(args)
        assert os.path.exists(os.path.join(out, "app_.env"))
