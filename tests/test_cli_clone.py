"""Tests for envoy.cli_clone command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from envoy.cli_clone import cmd_clone
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / "source.env"
    _write(str(p), "APP_HOST=localhost\nAPP_PORT=8080\nDB_URL=postgres://localhost/db\n")
    return str(p)


def make_args(source, destination, prefix=None, strip_prefix=False, rename=None):
    ns = argparse.Namespace(
        source=source,
        destination=destination,
        prefix=prefix,
        strip_prefix=strip_prefix,
        rename=rename,
    )
    return ns


class TestCmdClone:
    def test_exits_zero_on_success(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        args = make_args(tmp_env, dest)
        assert cmd_clone(args) == 0

    def test_creates_destination_file(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        cmd_clone(make_args(tmp_env, dest))
        assert os.path.exists(dest)

    def test_destination_contains_all_keys(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        cmd_clone(make_args(tmp_env, dest))
        parsed = parse_env_file(dest)
        assert "APP_HOST" in parsed
        assert "DB_URL" in parsed

    def test_prefix_filter_limits_keys(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        cmd_clone(make_args(tmp_env, dest, prefix="APP_"))
        parsed = parse_env_file(dest)
        assert "APP_HOST" in parsed
        assert "DB_URL" not in parsed

    def test_rename_flag_renames_key(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        cmd_clone(make_args(tmp_env, dest, rename=["APP_HOST=HOSTNAME"]))
        parsed = parse_env_file(dest)
        assert "HOSTNAME" in parsed
        assert parsed["HOSTNAME"] == "localhost"

    def test_invalid_rename_pair_exits_two(self, tmp_env, tmp_path):
        dest = str(tmp_path / "dest.env")
        args = make_args(tmp_env, dest, rename=["BADPAIR"])
        assert cmd_clone(args) == 2

    def test_missing_source_exits_one(self, tmp_path):
        dest = str(tmp_path / "dest.env")
        args = make_args("/no/such/file.env", dest)
        assert cmd_clone(args) == 1
