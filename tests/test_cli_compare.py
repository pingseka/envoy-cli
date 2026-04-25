"""Tests for envoy.cli_compare module."""
import os
import argparse
import pytest

from envoy.cli_compare import cmd_compare, register_commands


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"no_color": True, "all": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def tmp_env(tmp_path):
    return str(tmp_path)


class TestCmdCompare:
    def test_identical_files_exits_zero(self, tmp_env):
        p = os.path.join(tmp_env, "a.env")
        _write(p, "FOO=bar\n")
        args = make_args(base=p, target=p)
        assert cmd_compare(args) == 0

    def test_different_files_exits_nonzero(self, tmp_env):
        b = os.path.join(tmp_env, "b.env")
        t = os.path.join(tmp_env, "t.env")
        _write(b, "FOO=bar\n")
        _write(t, "FOO=baz\n")
        args = make_args(base=b, target=t)
        assert cmd_compare(args) == 1

    def test_missing_file_exits_one(self, tmp_env, capsys):
        b = os.path.join(tmp_env, "b.env")
        _write(b, "FOO=bar\n")
        args = make_args(base=b, target="/nonexistent/path.env")
        rc = cmd_compare(args)
        assert rc == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_prints_added_key(self, tmp_env, capsys):
        b = os.path.join(tmp_env, "b.env")
        t = os.path.join(tmp_env, "t.env")
        _write(b, "")
        _write(t, "NEW_KEY=hello\n")
        args = make_args(base=b, target=t)
        cmd_compare(args)
        out = capsys.readouterr().out
        assert "NEW_KEY" in out

    def test_prints_summary(self, tmp_env, capsys):
        b = os.path.join(tmp_env, "b.env")
        t = os.path.join(tmp_env, "t.env")
        _write(b, "FOO=1\n")
        _write(t, "BAR=2\n")
        args = make_args(base=b, target=t)
        cmd_compare(args)
        out = capsys.readouterr().out
        assert "added" in out

    def test_all_flag_includes_unchanged(self, tmp_env, capsys):
        p = os.path.join(tmp_env, "same.env")
        _write(p, "FOO=bar\n")
        args = make_args(base=p, target=p, **{"all": True})
        cmd_compare(args)
        out = capsys.readouterr().out
        assert "FOO" in out

    def test_register_commands_adds_compare(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        parsed = parser.parse_args(["compare", "a.env", "b.env"])
        assert parsed.base == "a.env"
        assert parsed.target == "b.env"
