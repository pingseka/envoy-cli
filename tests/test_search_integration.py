"""Integration tests for search: parse -> search -> display."""
from __future__ import annotations

import pytest

from envoy.parser import parse_env_file, serialize_env
from envoy.search import search_env


def _write(path, content):
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        (
            "DB_HOST=localhost\n"
            "DB_PORT=5432\n"
            "DB_PASSWORD=hunter2\n"
            "REDIS_URL=redis://localhost:6379\n"
            "APP_ENV=production\n"
        ),
    )
    return str(p)


class TestSearchIntegration:
    def test_parsed_env_search_by_prefix(self, env_file):
        env = parse_env_file(env_file)
        result = search_env(env, key_pattern="^DB_")
        keys = [m.key for m in result.matches]
        assert "DB_HOST" in keys
        assert "DB_PORT" in keys
        assert "DB_PASSWORD" in keys
        assert "REDIS_URL" not in keys

    def test_value_pattern_across_parsed_env(self, env_file):
        env = parse_env_file(env_file)
        result = search_env(env, value_pattern="localhost")
        keys = [m.key for m in result.matches]
        assert "DB_HOST" in keys
        assert "REDIS_URL" in keys
        assert "APP_ENV" not in keys

    def test_secret_detection_after_parse(self, env_file):
        env = parse_env_file(env_file)
        result = search_env(env, key_pattern="PASSWORD")
        assert result.matches[0].is_secret is True
        assert result.matches[0].display_value() == "***"

    def test_total_scanned_matches_env_size(self, env_file):
        env = parse_env_file(env_file)
        result = search_env(env, key_pattern=".*")
        assert result.total_scanned == len(env)
        assert result.match_count == len(env)
