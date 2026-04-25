"""Tests for envoy.cli_template module."""

import io
import os
import tempfile
import argparse
import pytest

from envoy.cli_template import cmd_render, register_commands


@pytest.fixture
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def make_args(**kwargs):
    defaults = {"file": "", "output": None, "var": None, "strict": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdRender:
    def test_renders_simple_substitution(self, tmp_env):
        path = tmp_env("BASE=http://localhost\nURL=${BASE}/api\n")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path)
        rc = cmd_render(args, out=out, err=err)
        assert rc == 0
        assert "http://localhost/api" in out.getvalue()

    def test_passes_extra_context_via_var(self, tmp_env):
        path = tmp_env("GREETING=Hello, ${NAME}!\n")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path, var=["NAME=World"])
        rc = cmd_render(args, out=out, err=err)
        assert rc == 0
        assert "Hello, World!" in out.getvalue()

    def test_warns_on_unresolved_variable(self, tmp_env):
        path = tmp_env("URL=${MISSING}/path\n")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path)
        rc = cmd_render(args, out=out, err=err)
        assert rc == 0
        assert "Warning" in err.getvalue()
        assert "MISSING" in err.getvalue()

    def test_strict_mode_returns_nonzero_on_unresolved(self, tmp_env):
        path = tmp_env("URL=${MISSING}/path\n")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path, strict=True)
        rc = cmd_render(args, out=out, err=err)
        assert rc == 2

    def test_file_not_found_returns_error(self, tmp_path):
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=str(tmp_path / "nonexistent.env"))
        rc = cmd_render(args, out=out, err=err)
        assert rc == 1
        assert "not found" in err.getvalue()

    def test_output_written_to_file(self, tmp_env, tmp_path):
        path = tmp_env("KEY=value\n")
        out_path = str(tmp_path / "rendered.env")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path, output=out_path)
        rc = cmd_render(args, out=out, err=err)
        assert rc == 0
        assert os.path.exists(out_path)
        assert "KEY=value" in open(out_path).read()

    def test_malformed_var_is_ignored(self, tmp_env):
        path = tmp_env("KEY=value\n")
        out, err = io.StringIO(), io.StringIO()
        args = make_args(file=path, var=["BADENTRY"])
        rc = cmd_render(args, out=out, err=err)
        assert rc == 0
        assert "Warning" in err.getvalue()


class TestRegisterCommands:
    def test_render_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_commands(subparsers)
        args = parser.parse_args(["render", "some.env"])
        assert args.file == "some.env"
        assert args.func is cmd_render
