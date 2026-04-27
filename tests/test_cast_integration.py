"""Integration tests: parse a real .env file then cast its values."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy.cast import CastType, cast_env
from envoy.parser import parse_env_file


def _write(path: str, content: str) -> None:
    Path(path).write_text(content)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        "PORT=3000\n"
        "DEBUG=false\n"
        "WORKERS=4\n"
        "RATIO=0.75\n"
        "ALLOWED_HOSTS=localhost,127.0.0.1,example.com\n"
        "APP_NAME=envoy\n",
    )
    return str(p)


class TestCastIntegration:
    def test_full_schema_round_trip(self, env_file):
        env = parse_env_file(env_file)
        schema = {
            "PORT": CastType.INTEGER,
            "DEBUG": CastType.BOOLEAN,
            "WORKERS": CastType.INTEGER,
            "RATIO": CastType.FLOAT,
            "ALLOWED_HOSTS": CastType.LIST,
            "APP_NAME": CastType.STRING,
        }
        result = cast_env(env, schema)
        assert result.has_errors is False
        vals = result.values
        assert vals["PORT"] == 3000
        assert vals["DEBUG"] is False
        assert vals["WORKERS"] == 4
        assert abs(vals["RATIO"] - 0.75) < 1e-9
        assert vals["ALLOWED_HOSTS"] == ["localhost", "127.0.0.1", "example.com"]
        assert vals["APP_NAME"] == "envoy"

    def test_partial_schema_ignores_unspecified_keys(self, env_file):
        env = parse_env_file(env_file)
        result = cast_env(env, {"PORT": CastType.INTEGER})
        assert list(result.values.keys()) == ["PORT"]

    def test_bad_value_captured_as_error(self, tmp_path):
        p = tmp_path / "bad.env"
        _write(str(p), "PORT=abc\nDEBUG=maybe\n")
        env = parse_env_file(str(p))
        result = cast_env(env, {"PORT": CastType.INTEGER, "DEBUG": CastType.BOOLEAN})
        assert result.has_errors is True
        assert len(result.errors()) == 2
