"""Integration tests: rename + parse roundtrip."""

import os
import pytest
from envoy.rename import rename_keys
from envoy.parser import parse_env_file, serialize_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def env_file(tmp_path):
    path = str(tmp_path / ".env")
    _write(path, "SECRET_KEY=abc123\nDEBUG=true\nDATABASE_URL=postgres://localhost/db\n")
    return path


class TestRenameIntegration:
    def test_value_preserved_after_rename(self, env_file):
        rename_keys(env_file, {"DATABASE_URL": "DB_URL"})
        data = parse_env_file(env_file)
        assert data["DB_URL"] == "postgres://localhost/db"

    def test_other_keys_unchanged_after_rename(self, env_file):
        rename_keys(env_file, {"DEBUG": "APP_DEBUG"})
        data = parse_env_file(env_file)
        assert data["SECRET_KEY"] == "abc123"
        assert data["DATABASE_URL"] == "postgres://localhost/db"

    def test_rename_chain_two_keys(self, env_file):
        rename_keys(env_file, {"SECRET_KEY": "APP_SECRET", "DEBUG": "APP_DEBUG"})
        data = parse_env_file(env_file)
        assert "SECRET_KEY" not in data
        assert "DEBUG" not in data
        assert data["APP_SECRET"] == "abc123"
        assert data["APP_DEBUG"] == "true"

    def test_serialize_then_rename_roundtrip(self, tmp_path):
        path = str(tmp_path / "round.env")
        original = {"FOO": "bar", "BAZ": "qux"}
        serialize_env(original, path)
        rename_keys(path, {"FOO": "FOO_RENAMED"})
        data = parse_env_file(path)
        assert "FOO_RENAMED" in data
        assert data["FOO_RENAMED"] == "bar"
        assert "FOO" not in data

    def test_dry_run_full_roundtrip(self, env_file):
        before = parse_env_file(env_file)
        rename_keys(env_file, {"SECRET_KEY": "APP_SECRET"}, dry_run=True)
        after = parse_env_file(env_file)
        assert before == after
