"""Unit tests for envoy.cli_transform."""
from __future__ import annotations

import argparse
import os

import pytest

from envoy.cli_transform import cmd_transform
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_env(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "GREETING=hello\nTAG=world\n")
    return path


def make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(file=None, operation="upper", keys=None, value=None, write=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdTransform:
    def test_exits_zero_on_success(self, tmp_env):
        args = make_args(file=tmp_env, operation="upper")
        assert cmd_transform(args) == 0

    def test_upper_operation_prints_changes(self, tmp_env, capsys):
        args = make_args(file=tmp_env, operation="upper")
        cmd_transform(args)
        out = capsys.readouterr().out
        assert "GREETING" in out or "HELLO" in out

    def test_write_flag_updates_file(self, tmp_env):
        args = make_args(file=tmp_env, operation="upper", write=True)
        cmd_transform(args)
        env = parse_env_file(tmp_env)
        assert env["GREETING"] == "HELLO"

    def test_no_write_does_not_modify_file(self, tmp_env):
        args = make_args(file=tmp_env, operation="upper", write=False)
        cmd_transform(args)
        env = parse_env_file(tmp_env)
        assert env["GREETING"] == "hello"

    def test_lower_operation(self, tmp_env):
        _write(tmp_env, "KEY=HELLO\n")
        args = make_args(file=tmp_env, operation="lower", write=True)
        cmd_transform(args)
        assert parse_env_file(tmp_env)["KEY"] == "hello"

    def test_prefix_operation(self, tmp_env):
        args = make_args(file=tmp_env, operation="prefix", value="pre_", write=True)
        cmd_transform(args)
        env = parse_env_file(tmp_env)
        assert env["GREETING"] == "pre_hello"

    def test_unknown_operation_exits_two(self, tmp_env):
        args = make_args(file=tmp_env, operation="bogus")
        assert cmd_transform(args) == 2

    def test_no_changes_exits_zero(self, tmp_env):
        _write(tmp_env, "KEY=ALREADY\n")
        args = make_args(file=tmp_env, operation="upper")
        assert cmd_transform(args) == 0
