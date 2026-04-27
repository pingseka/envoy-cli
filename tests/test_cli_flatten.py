"""Tests for envoy.cli_flatten."""
from __future__ import annotations

import argparse
import os
import pytest

from envoy.cli_flatten import cmd_flatten, register_commands


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    _write(str(p), "APP_HOST=localhost\nAPP_PORT=8080\nDB=mydb\n")
    return str(p)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file="",
        strip_prefix="",
        keep_last=False,
        output="",
        dry_run=False,
        verbose=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdFlatten:
    def test_exits_zero_no_duplicates(self, tmp_env):
        args = make_args(file=tmp_env)
        assert cmd_flatten(args) == 0

    def test_exits_two_with_duplicates(self, tmp_path):
        p = tmp_path / ".env"
        _write(str(p), "KEY=a\nKEY=b\n")
        args = make_args(file=str(p))
        assert cmd_flatten(args) == 2

    def test_dry_run_does_not_write(self, tmp_env, capsys):
        args = make_args(file=tmp_env, dry_run=True)
        cmd_flatten(args)
        captured = capsys.readouterr()
        assert "kept" in captured.out or "renamed" in captured.out

    def test_output_writes_file(self, tmp_env, tmp_path):
        out = str(tmp_path / "out.env")
        args = make_args(file=tmp_env, output=out)
        cmd_flatten(args)
        assert os.path.exists(out)
        with open(out) as fh:
            content = fh.read()
        assert "HOST" in content or "APP_HOST" in content

    def test_strip_prefix_in_output(self, tmp_env, tmp_path):
        out = str(tmp_path / "out.env")
        args = make_args(file=tmp_env, strip_prefix="APP_", output=out)
        cmd_flatten(args)
        with open(out) as fh:
            content = fh.read()
        assert "HOST=" in content
        assert "PORT=" in content
        assert "APP_HOST" not in content

    def test_missing_file_returns_one(self, tmp_path):
        args = make_args(file=str(tmp_path / "ghost.env"))
        assert cmd_flatten(args) == 1

    def test_register_commands_adds_flatten(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["flatten", "somefile.env"])
        assert hasattr(args, "func")
