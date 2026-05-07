"""Tests for envoy.prefix module."""

import os
import tempfile
import pytest

from envoy.parser import parse_env_file
from envoy.prefix import PrefixStatus, add_prefix, remove_prefix


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def env_file(tmp_dir):
    path = os.path.join(tmp_dir, ".env")
    _write(path, "APP_HOST=localhost\nAPP_PORT=8080\nDEBUG=true\n")
    return path


class TestAddPrefix:
    def test_adds_prefix_to_all_keys(self, env_file):
        result = add_prefix(env_file, "MY_")
        keys = [e.new_key for e in result.entries]
        assert "MY_APP_HOST" in keys
        assert "MY_APP_PORT" in keys
        assert "MY_DEBUG" in keys

    def test_already_prefixed_keys_are_skipped(self, env_file):
        result = add_prefix(env_file, "APP_")
        skipped = [e.original_key for e in result.skipped()]
        assert "APP_HOST" in skipped
        assert "APP_PORT" in skipped

    def test_changed_count_excludes_already_prefixed(self, env_file):
        result = add_prefix(env_file, "APP_")
        # APP_HOST and APP_PORT already have prefix; DEBUG does not
        assert len(result.changed()) == 1
        assert result.changed()[0].original_key == "DEBUG"

    def test_output_file_is_updated(self, env_file):
        add_prefix(env_file, "MY_")
        env = parse_env_file(env_file)
        assert "MY_APP_HOST" in env
        assert "MY_DEBUG" in env
        assert "APP_HOST" not in env

    def test_values_preserved_after_prefix(self, env_file):
        add_prefix(env_file, "X_")
        env = parse_env_file(env_file)
        assert env["X_APP_HOST"] == "localhost"
        assert env["X_APP_PORT"] == "8080"

    def test_summary_string(self, env_file):
        result = add_prefix(env_file, "MY_")
        assert "renamed" in result.summary()
        assert "skipped" in result.summary()

    def test_custom_output_path(self, tmp_dir, env_file):
        out = os.path.join(tmp_dir, "out.env")
        result = add_prefix(env_file, "P_", output_path=out)
        assert result.output_path == out
        assert os.path.exists(out)
        env = parse_env_file(out)
        assert "P_APP_HOST" in env


class TestRemovePrefix:
    def test_removes_matching_prefix(self, env_file):
        result = remove_prefix(env_file, "APP_")
        new_keys = [e.new_key for e in result.entries]
        assert "HOST" in new_keys
        assert "PORT" in new_keys

    def test_non_matching_keys_are_skipped(self, env_file):
        result = remove_prefix(env_file, "APP_")
        skipped = [e.original_key for e in result.skipped()]
        assert "DEBUG" in skipped

    def test_output_file_reflects_removal(self, env_file):
        remove_prefix(env_file, "APP_")
        env = parse_env_file(env_file)
        assert "HOST" in env
        assert "PORT" in env
        assert "DEBUG" in env
        assert "APP_HOST" not in env

    def test_values_intact_after_removal(self, env_file):
        remove_prefix(env_file, "APP_")
        env = parse_env_file(env_file)
        assert env["HOST"] == "localhost"
        assert env["PORT"] == "8080"

    def test_status_removed_for_matched_keys(self, env_file):
        result = remove_prefix(env_file, "APP_")
        removed = [e for e in result.entries if e.status == PrefixStatus.REMOVED]
        assert len(removed) == 2
