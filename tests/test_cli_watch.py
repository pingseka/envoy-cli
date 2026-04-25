"""Tests for envoy.cli_watch."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy.cli_watch import cmd_watch, register_commands


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def make_args(files, interval=1.0, verbose=False):
    return Namespace(files=files, interval=interval, verbose=verbose)


class TestCmdWatch:
    def test_exits_when_no_files(self, capsys):
        args = make_args(files=[])
        with pytest.raises(SystemExit) as exc:
            cmd_watch(args)
        assert exc.value.code == 1

    def test_prints_watching_message(self, tmp_env, capsys):
        path = tmp_env("w.env", "KEY=val\n")
        args = make_args(files=[path])
        with patch("envoy.cli_watch.EnvWatcher") as MockWatcher:
            instance = MockWatcher.return_value
            instance.watch = MagicMock()
            instance.on_change = MagicMock()
            cmd_watch(args)
        out = capsys.readouterr().out
        assert "Watching" in out
        assert path in out

    def test_watch_called_with_no_max(self, tmp_env):
        path = tmp_env("v.env", "A=1\n")
        args = make_args(files=[path])
        with patch("envoy.cli_watch.EnvWatcher") as MockWatcher:
            instance = MockWatcher.return_value
            instance.watch = MagicMock()
            instance.on_change = MagicMock()
            cmd_watch(args)
            instance.watch.assert_called_once_with()

    def test_watcher_created_with_correct_interval(self, tmp_env):
        path = tmp_env("u.env", "B=2\n")
        args = make_args(files=[path], interval=2.5)
        with patch("envoy.cli_watch.EnvWatcher") as MockWatcher:
            instance = MockWatcher.return_value
            instance.watch = MagicMock()
            instance.on_change = MagicMock()
            cmd_watch(args)
            MockWatcher.assert_called_once_with([path], interval=2.5)


class TestRegisterCommands:
    def test_registers_watch_subcommand(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["watch", "some.env", "--interval", "0.5"])
        assert args.files == ["some.env"]
        assert args.interval == 0.5

    def test_verbose_flag_defaults_false(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["watch", "x.env"])
        assert args.verbose is False

    def test_verbose_flag_set(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["watch", "x.env", "-v"])
        assert args.verbose is True
