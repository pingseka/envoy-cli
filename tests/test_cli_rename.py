"""Tests for envoy.cli_rename module."""

import argparse
import os
import pytest
from envoy.cli_rename import cmd_rename, register_commands


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "",
        "rename": [],
        "dry_run": False,
        "overwrite": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def tmp_env(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "OLD_KEY=hello\nKEEP=world\n")
    return path


class TestCmdRename:
    def test_renames_key_exits_zero(self, tmp_env):
        args = make_args(file=tmp_env, rename=["OLD_KEY", "NEW_KEY"])
        rc = cmd_rename(args)
        assert rc == 0

    def test_missing_key_exits_one(self, tmp_env):
        args = make_args(file=tmp_env, rename=["GHOST", "NEW_KEY"])
        rc = cmd_rename(args)
        assert rc == 1

    def test_odd_rename_args_exits_two(self, tmp_env):
        args = make_args(file=tmp_env, rename=["ONLY_ONE"])
        rc = cmd_rename(args)
        assert rc == 2

    def test_dry_run_does_not_modify_file(self, tmp_env):
        args = make_args(file=tmp_env, rename=["OLD_KEY", "NEW_KEY"], dry_run=True)
        cmd_rename(args)
        from envoy.parser import parse_env_file
        data = parse_env_file(tmp_env)
        assert "OLD_KEY" in data

    def test_register_commands_adds_rename(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args([
            "rename", "/fake/.env", "OLD", "NEW",
        ])
        assert args.rename == ["OLD", "NEW"]
        assert args.dry_run is False
        assert args.overwrite is False

    def test_register_commands_dry_run_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["rename", "/f", "A", "B", "--dry-run"])
        assert args.dry_run is True

    def test_register_commands_overwrite_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["rename", "/f", "A", "B", "--overwrite"])
        assert args.overwrite is True
