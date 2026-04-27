"""Integration tests for rotate: parser round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.parser import parse_env_file
from envoy.rotate import apply_rotation, rotate_keys


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    _write(p, "FOO=bar\nBAZ=qux\nSECRET_KEY=topsecret\n")
    return p


class TestRotateIntegration:
    def test_value_preserved_after_rotate_and_reparse(self, env_file):
        result = rotate_keys(env_file, {"FOO": "FOO_RENAMED"})
        apply_rotation(env_file, result)
        reparsed = parse_env_file(env_file)
        assert reparsed["FOO_RENAMED"] == "bar"

    def test_other_keys_intact_after_reparse(self, env_file):
        result = rotate_keys(env_file, {"FOO": "FOO_RENAMED"})
        apply_rotation(env_file, result)
        reparsed = parse_env_file(env_file)
        assert reparsed["BAZ"] == "qux"
        assert reparsed["SECRET_KEY"] == "topsecret"

    def test_multiple_renames_persist(self, env_file):
        result = rotate_keys(env_file, {"FOO": "FOO_V2", "BAZ": "BAZ_V2"})
        apply_rotation(env_file, result)
        reparsed = parse_env_file(env_file)
        assert "FOO_V2" in reparsed
        assert "BAZ_V2" in reparsed
        assert "FOO" not in reparsed
        assert "BAZ" not in reparsed

    def test_no_duplicate_keys_after_rotate(self, env_file):
        result = rotate_keys(env_file, {"FOO": "FOO_RENAMED"})
        apply_rotation(env_file, result)
        reparsed = parse_env_file(env_file)
        keys = list(reparsed.keys())
        assert len(keys) == len(set(keys))
