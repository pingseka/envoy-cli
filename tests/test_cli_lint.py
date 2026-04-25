"""Tests for envoy.cli_lint module."""

import os
import sys
import tempfile
import argparse
import pytest

from envoy.cli_lint import cmd_lint, register_commands


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".env")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "quiet": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCmdLint:
    def test_clean_file_exits_zero(self, capsys):
        path = _write("APP=hello\nDEBUG=true\n")
        args = make_args(files=[path])
        with pytest.raises(SystemExit) as exc:
            cmd_lint(args)
        assert exc.value.code == 0

    def test_clean_file_prints_ok(self, capsys):
        path = _write("APP=hello\n")
        args = make_args(files=[path])
        with pytest.raises(SystemExit):
            cmd_lint(args)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_quiet_suppresses_ok(self, capsys):
        path = _write("APP=hello\n")
        args = make_args(files=[path], quiet=True)
        with pytest.raises(SystemExit):
            cmd_lint(args)
        out = capsys.readouterr().out
        assert "OK" not in out

    def test_error_file_exits_one(self):
        path = _write("BADLINE\n")
        args = make_args(files=[path])
        with pytest.raises(SystemExit) as exc:
            cmd_lint(args)
        assert exc.value.code == 1

    def test_missing_file_exits_two(self):
        args = make_args(files=["/nonexistent/path/.env"])
        with pytest.raises(SystemExit) as exc:
            cmd_lint(args)
        assert exc.value.code == 2

    def test_warning_only_exits_zero(self):
        # lowercase key → warning, not error
        path = _write("app_name=hello\n")
        args = make_args(files=[path])
        with pytest.raises(SystemExit) as exc:
            cmd_lint(args)
        assert exc.value.code == 0

    def test_multiple_files_all_clean(self):
        p1 = _write("A=1\n")
        p2 = _write("B=2\n")
        args = make_args(files=[p1, p2])
        with pytest.raises(SystemExit) as exc:
            cmd_lint(args)
        assert exc.value.code == 0


class TestRegisterCommands:
    def test_lint_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        parsed = parser.parse_args(["lint", "some.env"])
        assert parsed.files == ["some.env"]

    def test_quiet_flag_default_false(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        parsed = parser.parse_args(["lint", "some.env"])
        assert parsed.quiet is False
