"""Tests for envoy.cli_search."""
from __future__ import annotations

import argparse
import os
import tempfile

import pytest

from envoy.cli_search import cmd_search


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        "APP_NAME=myapp\nSECRET_KEY=s3cr3t\nPORT=9000\nDEBUG=false\n",
    )
    return str(p)


def make_args(**kwargs):
    defaults = {
        "file": "",
        "key": "",
        "value": "",
        "case_sensitive": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdSearch:
    def test_exits_zero_on_match(self, tmp_env):
        args = make_args(file=tmp_env, key="APP")
        assert cmd_search(args) == 0

    def test_exits_one_on_no_match(self, tmp_env):
        args = make_args(file=tmp_env, key="NONEXISTENT")
        assert cmd_search(args) == 1

    def test_exits_one_missing_file(self, tmp_path):
        args = make_args(file=str(tmp_path / "ghost.env"), key="APP")
        assert cmd_search(args) == 1

    def test_exits_one_no_patterns(self, tmp_env):
        args = make_args(file=tmp_env)
        assert cmd_search(args) == 1

    def test_value_search_finds_match(self, tmp_env):
        args = make_args(file=tmp_env, value="9000")
        assert cmd_search(args) == 0

    def test_combined_key_value_search(self, tmp_env):
        args = make_args(file=tmp_env, key="PORT", value="9000")
        assert cmd_search(args) == 0

    def test_combined_no_match_when_value_wrong(self, tmp_env):
        args = make_args(file=tmp_env, key="PORT", value="1234")
        assert cmd_search(args) == 1

    def test_output_contains_key(self, tmp_env, capsys):
        args = make_args(file=tmp_env, key="APP_NAME")
        cmd_search(args)
        captured = capsys.readouterr()
        assert "APP_NAME" in captured.out

    def test_secret_value_masked_in_output(self, tmp_env, capsys):
        args = make_args(file=tmp_env, key="SECRET_KEY")
        cmd_search(args)
        captured = capsys.readouterr()
        assert "s3cr3t" not in captured.out
        assert "***" in captured.out
