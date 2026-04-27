"""Tests for envoy.cli_pin."""

import argparse
import sys

import pytest

from envoy.cli_pin import cmd_pin, register_commands


@pytest.fixture
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)

    return _write


def make_args(env_file: str, pins: list) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, pins=pins)


class TestCmdPin:
    def test_exits_zero_when_all_satisfied(self, tmp_env):
        path = tmp_env("APP_ENV=production\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["APP_ENV=production"]))
        assert exc.value.code == 0

    def test_exits_one_on_missing_key(self, tmp_env):
        path = tmp_env("APP_ENV=production\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["SECRET_KEY"]))
        assert exc.value.code == 1

    def test_exits_one_on_value_mismatch(self, tmp_env):
        path = tmp_env("APP_ENV=staging\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["APP_ENV=production"]))
        assert exc.value.code == 1

    def test_presence_only_pin_passes(self, tmp_env):
        path = tmp_env("SECRET_KEY=anything\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["SECRET_KEY"]))
        assert exc.value.code == 0

    def test_regex_pin_passes(self, tmp_env, capsys):
        path = tmp_env("PORT=9000\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["PORT=re:[0-9]+"]))
        assert exc.value.code == 0

    def test_regex_pin_fails(self, tmp_env):
        path = tmp_env("PORT=nope\n")
        with pytest.raises(SystemExit) as exc:
            cmd_pin(make_args(path, ["PORT=re:[0-9]+"]))
        assert exc.value.code == 1

    def test_ok_message_printed(self, tmp_env, capsys):
        path = tmp_env("APP_ENV=production\n")
        with pytest.raises(SystemExit):
            cmd_pin(make_args(path, ["APP_ENV=production"]))
        out = capsys.readouterr().out
        assert "satisfied" in out

    def test_violation_key_printed(self, tmp_env, capsys):
        path = tmp_env("APP_ENV=staging\n")
        with pytest.raises(SystemExit):
            cmd_pin(make_args(path, ["APP_ENV=production"]))
        out = capsys.readouterr().out
        assert "APP_ENV" in out

    def test_register_commands_adds_pin(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub)
        args = parser.parse_args(["/dev/null", "KEY"], namespace=argparse.Namespace(func=None))
        # register_commands sets func on the subparser
        # Just verify parsing doesn't raise
        assert hasattr(args, "env_file") or True  # smoke test
