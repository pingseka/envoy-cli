"""Tests for envoy.cli_interpolate."""
from __future__ import annotations

import argparse
import os
import tempfile

import pytest

from envoy.cli_interpolate import cmd_interpolate


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"file": "", "context": None, "check": False, "inplace": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    return str(p)


class TestCmdInterpolate:
    def test_exits_zero_when_all_resolved(self, tmp_env):
        _write(tmp_env, "BASE=hello\nGREET=${BASE} world\n")
        rc = cmd_interpolate(make_args(file=tmp_env))
        assert rc == 0

    def test_exits_one_when_unresolved(self, tmp_env):
        _write(tmp_env, "URL=http://${MISSING}\n")
        rc = cmd_interpolate(make_args(file=tmp_env))
        assert rc == 1

    def test_check_flag_exits_zero_when_resolved(self, tmp_env):
        _write(tmp_env, "A=hello\nB=${A}\n")
        rc = cmd_interpolate(make_args(file=tmp_env, check=True))
        assert rc == 0

    def test_check_flag_exits_one_when_unresolved(self, tmp_env):
        _write(tmp_env, "URL=${GHOST}\n")
        rc = cmd_interpolate(make_args(file=tmp_env, check=True))
        assert rc == 1

    def test_inplace_writes_resolved_values(self, tmp_env):
        _write(tmp_env, "HOST=localhost\nURL=http://${HOST}\n")
        rc = cmd_interpolate(make_args(file=tmp_env, inplace=True))
        assert rc == 0
        with open(tmp_env) as fh:
            content = fh.read()
        assert "localhost" in content
        assert "http://localhost" in content

    def test_context_file_used_for_resolution(self, tmp_env, tmp_path):
        ctx = str(tmp_path / "ctx.env")
        _write(tmp_env, "URL=http://${HOST}\n")
        _write(ctx, "HOST=example.com\n")
        rc = cmd_interpolate(make_args(file=tmp_env, context=ctx))
        assert rc == 0

    def test_missing_file_returns_one(self, tmp_path):
        rc = cmd_interpolate(make_args(file=str(tmp_path / "ghost.env")))
        assert rc == 1

    def test_missing_context_file_returns_one(self, tmp_env):
        _write(tmp_env, "A=1\n")
        rc = cmd_interpolate(
            make_args(file=tmp_env, context="/nonexistent/ctx.env")
        )
        assert rc == 1
