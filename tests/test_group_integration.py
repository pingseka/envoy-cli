"""Integration tests: group -> serialize round-trip."""
from __future__ import annotations

import os
import tempfile
import pytest

from envoy.parser import parse_env_file, serialize_env
from envoy.group import group_by_prefix, group_by_pattern


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        "DB_HOST=localhost\nDB_PORT=5432\nCACHE_URL=redis://localhost\nAPP_NAME=envoy\nDEBUG=true\n",
    )
    return str(p)


class TestGroupIntegration:
    def test_prefix_groups_sum_to_total(self, env_file):
        env = parse_env_file(env_file)
        result = group_by_prefix(env, ["DB_", "CACHE_"])
        grouped_total = sum(len(v) for v in result.groups.values())
        assert grouped_total + len(result.ungrouped) == len(env)

    def test_serialize_grouped_keys_round_trips(self, env_file, tmp_path):
        env = parse_env_file(env_file)
        result = group_by_prefix(env, ["DB_"], strip_prefix=False)
        out_path = str(tmp_path / "db.env")
        serialized = serialize_env(result.groups["DB_"])
        _write(out_path, serialized)
        reparsed = parse_env_file(out_path)
        assert reparsed["DB_HOST"] == "localhost"
        assert reparsed["DB_PORT"] == "5432"

    def test_pattern_group_all_keys_accounted(self, env_file):
        env = parse_env_file(env_file)
        result = group_by_pattern(env, {"db": r"^DB_", "cache": r"^CACHE_"})
        all_keys = set()
        for grp in result.groups.values():
            all_keys.update(grp.keys())
        all_keys.update(result.ungrouped.keys())
        assert all_keys == set(env.keys())
