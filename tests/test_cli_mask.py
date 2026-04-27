"""Tests for envoy.cli_mask module."""

from __future__ import annotations

import argparse
import os
import sys

import pytest

from envoy.cli_mask import cmd_mask


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_env(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "APP_NAME=myapp\nSECRET_KEY=s3cr3t\nDEBUG=false\n")
    return path


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "",
        "keys": None,
        "pattern": None,
        "auto_secrets": False,
        "output": None,
        "verbose": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdMask:
    def test_exits_zero_on_success(self, tmp_env, capsys):
        args = make_args(file=tmp_env, keys=["SECRET_KEY"])
        assert cmd_mask(args) == 0

    def test_prints_masked_output(self, tmp_env, capsys):
        args = make_args(file=tmp_env, keys=["SECRET_KEY"])
        cmd_mask(args)
        out = capsys.readouterr().out
        assert "SECRET_KEY=***" in out

    def test_unmasked_keys_printed_plainly(self, tmp_env, capsys):
        args = make_args(file=tmp_env, keys=["SECRET_KEY"])
        cmd_mask(args)
        out = capsys.readouterr().out
        assert "APP_NAME=myapp" in out

    def test_verbose_prints_summary(self, tmp_env, capsys):
        args = make_args(file=tmp_env, keys=["SECRET_KEY"], verbose=True)
        cmd_mask(args)
        out = capsys.readouterr().out
        assert "masked" in out

    def test_no_keys_returns_error(self, tmp_env, capsys):
        args = make_args(file=tmp_env)
        rc = cmd_mask(args)
        assert rc == 1

    def test_missing_file_returns_error(self, tmp_path, capsys):
        args = make_args(file=str(tmp_path / "missing.env"), keys=["KEY"])
        rc = cmd_mask(args)
        assert rc == 1

    def test_output_writes_file(self, tmp_env, tmp_path, capsys):
        out_path = str(tmp_path / "masked.env")
        args = make_args(file=tmp_env, keys=["SECRET_KEY"], output=out_path)
        rc = cmd_mask(args)
        assert rc == 0
        assert os.path.exists(out_path)
        with open(out_path) as fh:
            content = fh.read()
        assert "SECRET_KEY=***" in content

    def test_pattern_arg_masks_matching(self, tmp_env, capsys):
        args = make_args(file=tmp_env, pattern=r"SECRET")
        rc = cmd_mask(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "SECRET_KEY=***" in out
