"""Integration tests: transform -> serialize -> reparse round-trip."""
from __future__ import annotations

import os

import pytest

from envoy.parser import parse_env_file, serialize_env
from envoy.transform import transform_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def env_file(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "DB_HOST=localhost\nDB_PASS=secret\nAPP_ENV=development\n")
    return path


class TestTransformIntegration:
    def test_upper_round_trip(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        serialized = serialize_env(result.env)
        with open(env_file, "w") as fh:
            fh.write(serialized)
        reparsed = parse_env_file(env_file)
        assert reparsed["DB_HOST"] == "LOCALHOST"
        assert reparsed["APP_ENV"] == "DEVELOPMENT"

    def test_other_keys_intact_after_partial_transform(self, env_file):
        result = transform_env(
            env_file, lambda k, v: v.upper(), keys=["DB_HOST"]
        )
        serialized = serialize_env(result.env)
        with open(env_file, "w") as fh:
            fh.write(serialized)
        reparsed = parse_env_file(env_file)
        assert reparsed["DB_PASS"] == "secret"  # untouched
        assert reparsed["DB_HOST"] == "LOCALHOST"

    def test_strip_removes_surrounding_whitespace(self, env_file):
        _write(env_file, "KEY=  spaced  \n")
        result = transform_env(env_file, lambda k, v: v.strip())
        assert result.env["KEY"] == "spaced"
