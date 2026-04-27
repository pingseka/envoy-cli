"""Tests for envoy.cli_cast module."""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import pytest

from envoy.cli_cast import cmd_cast, _parse_schema_arg
from envoy.cast import CastType


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    _write(str(p), "PORT=8080\nDEBUG=true\nTAGS=a,b,c\n")
    return str(p)


def make_args(env_file: str, schema: list) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, schema=schema)


class TestCmdCast:
    def test_exits_zero_on_success(self, tmp_env, capsys):
        args = make_args(tmp_env, ["PORT:int", "DEBUG:bool", "TAGS:list"])
        rc = cmd_cast(args)
        assert rc == 0

    def test_prints_cast_results(self, tmp_env, capsys):
        args = make_args(tmp_env, ["PORT:int"])
        cmd_cast(args)
        out = capsys.readouterr().out
        assert "PORT" in out

    def test_exits_one_on_missing_file(self, tmp_path, capsys):
        args = make_args(str(tmp_path / "missing.env"), ["PORT:int"])
        rc = cmd_cast(args)
        assert rc == 1

    def test_exits_one_on_cast_failure(self, tmp_path, capsys):
        p = tmp_path / ".env"
        _write(str(p), "PORT=notanumber\n")
        args = make_args(str(p), ["PORT:int"])
        rc = cmd_cast(args)
        assert rc == 1

    def test_exits_one_on_bad_schema(self, tmp_env, capsys):
        args = make_args(tmp_env, ["PORT:unknowntype"])
        rc = cmd_cast(args)
        assert rc == 1

    def test_exits_one_on_malformed_schema(self, tmp_env, capsys):
        args = make_args(tmp_env, ["PORTint"])  # missing colon
        rc = cmd_cast(args)
        assert rc == 1


class TestParseSchemaArg:
    def test_parses_int(self):
        schema = _parse_schema_arg(["PORT:int"])
        assert schema["PORT"] == CastType.INTEGER

    def test_parses_bool(self):
        schema = _parse_schema_arg(["DEBUG:boolean"])
        assert schema["DEBUG"] == CastType.BOOLEAN

    def test_parses_list(self):
        schema = _parse_schema_arg(["TAGS:list"])
        assert schema["TAGS"] == CastType.LIST

    def test_parses_float(self):
        schema = _parse_schema_arg(["RATE:float"])
        assert schema["RATE"] == CastType.FLOAT

    def test_parses_string(self):
        schema = _parse_schema_arg(["NAME:string"])
        assert schema["NAME"] == CastType.STRING

    def test_raises_on_unknown_type(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_schema_arg(["X:unknown"])

    def test_raises_on_missing_colon(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_schema_arg(["Xint"])
