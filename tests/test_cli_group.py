"""Tests for envoy.cli_group module."""
from __future__ import annotations

import os
import tempfile
import pytest

from envoy.cli_group import cmd_group


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        "DB_HOST=localhost\nDB_PORT=5432\nCACHE_URL=redis://localhost\nAPP_NAME=envoy\n",
    )
    return str(p)


def make_args(**kwargs):
    import argparse
    defaults = dict(file=None, prefix=None, pattern=None, strip_prefix=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdGroup:
    def test_exits_zero_with_prefix(self, tmp_env, capsys):
        args = make_args(file=tmp_env, prefix=["DB_"])
        rc = cmd_group(args)
        assert rc == 0

    def test_output_contains_group_name(self, tmp_env, capsys):
        args = make_args(file=tmp_env, prefix=["DB_"])
        cmd_group(args)
        out = capsys.readouterr().out
        assert "DB_" in out

    def test_output_contains_ungrouped(self, tmp_env, capsys):
        args = make_args(file=tmp_env, prefix=["DB_"])
        cmd_group(args)
        out = capsys.readouterr().out
        assert "ungrouped" in out

    def test_exits_one_on_missing_file(self, capsys):
        args = make_args(file="/nonexistent/.env", prefix=["DB_"])
        rc = cmd_group(args)
        assert rc == 1

    def test_pattern_mode_exits_zero(self, tmp_env, capsys):
        args = make_args(file=tmp_env, pattern=["db=^DB_", "cache=^CACHE_"])
        rc = cmd_group(args)
        assert rc == 0

    def test_pattern_bad_format_exits_one(self, tmp_env, capsys):
        args = make_args(file=tmp_env, pattern=["nodivider"])
        rc = cmd_group(args)
        assert rc == 1

    def test_strip_prefix_in_output(self, tmp_env, capsys):
        args = make_args(file=tmp_env, prefix=["DB_"], strip_prefix=True)
        cmd_group(args)
        out = capsys.readouterr().out
        assert "HOST" in out

    def test_summary_line_printed(self, tmp_env, capsys):
        args = make_args(file=tmp_env, prefix=["DB_"])
        cmd_group(args)
        out = capsys.readouterr().out
        assert "Summary" in out
