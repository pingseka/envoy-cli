"""Integration tests: mask -> serialize -> re-parse round trip."""

from __future__ import annotations

import os

import pytest

from envoy.mask import mask_env, MASK_PLACEHOLDER
from envoy.parser import parse_env_file, serialize_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def env_file(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "API_KEY=abc123\nHOST=localhost\nDB_PASS=secret\n")
    return path


class TestMaskIntegration:
    def test_masked_file_can_be_reparsed(self, env_file, tmp_path):
        result = mask_env(env_file, keys=["API_KEY", "DB_PASS"])
        out_path = str(tmp_path / "masked.env")
        with open(out_path, "w") as fh:
            fh.write(serialize_env(result.masked_env))
        reparsed = parse_env_file(out_path)
        assert reparsed["API_KEY"] == MASK_PLACEHOLDER
        assert reparsed["DB_PASS"] == MASK_PLACEHOLDER
        assert reparsed["HOST"] == "localhost"

    def test_unmasked_keys_unchanged_after_round_trip(self, env_file, tmp_path):
        result = mask_env(env_file, keys=["API_KEY"])
        out_path = str(tmp_path / "masked.env")
        with open(out_path, "w") as fh:
            fh.write(serialize_env(result.masked_env))
        reparsed = parse_env_file(out_path)
        assert reparsed["HOST"] == "localhost"
        assert reparsed["DB_PASS"] == "secret"

    def test_auto_secrets_round_trip(self, env_file, tmp_path):
        result = mask_env(env_file, auto_secrets=True)
        out_path = str(tmp_path / "masked.env")
        with open(out_path, "w") as fh:
            fh.write(serialize_env(result.masked_env))
        reparsed = parse_env_file(out_path)
        # API_KEY and DB_PASS are secret-like keys
        assert reparsed["API_KEY"] == MASK_PLACEHOLDER
        assert reparsed["DB_PASS"] == MASK_PLACEHOLDER
