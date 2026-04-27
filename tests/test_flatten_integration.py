"""Integration tests: flatten -> serialize -> re-parse round-trip."""
from __future__ import annotations

import os
import pytest

from envoy.flatten import flatten_env
from envoy.parser import parse_env_file, serialize_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    _write(
        str(p),
        "PROD_DB_HOST=db.prod.example.com\n"
        "PROD_DB_PORT=5432\n"
        "PROD_SECRET_KEY=supersecret\n"
        "UNRELATED=value\n",
    )
    return str(p)


class TestFlattenIntegration:
    def test_round_trip_preserves_values(self, env_file, tmp_path):
        result = flatten_env(env_file, strip_prefix="PROD_")
        out = str(tmp_path / "flat.env")
        with open(out, "w") as fh:
            fh.write(serialize_env(result.to_dict()))
        reparsed = parse_env_file(out)
        assert reparsed["DB_HOST"] == "db.prod.example.com"
        assert reparsed["DB_PORT"] == "5432"
        assert reparsed["SECRET_KEY"] == "supersecret"
        assert reparsed["UNRELATED"] == "value"

    def test_duplicate_removal_round_trip(self, tmp_path):
        p = tmp_path / ".env"
        _write(str(p), "FOO=first\nBAR=bar\nFOO=second\n")
        result = flatten_env(str(p), keep_first=True)
        out = str(tmp_path / "deduped.env")
        with open(out, "w") as fh:
            fh.write(serialize_env(result.to_dict()))
        reparsed = parse_env_file(out)
        assert reparsed["FOO"] == "first"
        assert reparsed["BAR"] == "bar"
        assert len(reparsed) == 2

    def test_no_prefix_match_keeps_all_keys(self, env_file):
        result = flatten_env(env_file, strip_prefix="NONEXISTENT_")
        d = result.to_dict()
        assert "PROD_DB_HOST" in d
        assert "UNRELATED" in d
        assert len(result.renamed()) == 0
