"""Tests for envoy.tag."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from envoy.tag import TagStatus, keys_for_tag, tag_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "DB_PASSWORD=secret\nAPI_KEY=abc123\nDEBUG=true\n")
    return p


@pytest.fixture()
def meta_file(tmp_dir):
    return os.path.join(tmp_dir, ".env.tags.json")


# ---------------------------------------------------------------------------
# TagResult helpers
# ---------------------------------------------------------------------------

class TestTagResult:
    def test_tagged_entries_filtered(self, env_file, meta_file):
        result = tag_keys(env_file, {"DB_PASSWORD": ["secret"]}, meta_path=meta_file)
        assert len(result.tagged()) == 1
        assert result.tagged()[0].key == "DB_PASSWORD"

    def test_not_found_entries_filtered(self, env_file, meta_file):
        result = tag_keys(env_file, {"MISSING_KEY": ["label"]}, meta_path=meta_file)
        assert len(result.not_found()) == 1

    def test_summary_string(self, env_file, meta_file):
        result = tag_keys(env_file, {"API_KEY": ["public"], "GHOST": ["x"]}, meta_path=meta_file)
        assert "1 tagged" in result.summary()
        assert "1 not found" in result.summary()


# ---------------------------------------------------------------------------
# tag_keys behaviour
# ---------------------------------------------------------------------------

class TestTagKeys:
    def test_creates_meta_file(self, env_file, meta_file):
        tag_keys(env_file, {"DEBUG": ["flag"]}, meta_path=meta_file)
        assert os.path.exists(meta_file)

    def test_meta_file_contains_tag(self, env_file, meta_file):
        tag_keys(env_file, {"DEBUG": ["flag"]}, meta_path=meta_file)
        data = json.loads(Path(meta_file).read_text())
        assert "flag" in data["DEBUG"]

    def test_already_tagged_not_duplicated(self, env_file, meta_file):
        tag_keys(env_file, {"DB_PASSWORD": ["secret"]}, meta_path=meta_file)
        result2 = tag_keys(env_file, {"DB_PASSWORD": ["secret"]}, meta_path=meta_file)
        assert result2.entries[0].status == TagStatus.ALREADY_TAGGED
        data = json.loads(Path(meta_file).read_text())
        assert data["DB_PASSWORD"].count("secret") == 1

    def test_missing_key_returns_not_found(self, env_file, meta_file):
        result = tag_keys(env_file, {"NO_SUCH": ["x"]}, meta_path=meta_file)
        assert result.entries[0].status == TagStatus.NOT_FOUND

    def test_multiple_tags_on_same_key(self, env_file, meta_file):
        result = tag_keys(env_file, {"API_KEY": ["public", "readonly"]}, meta_path=meta_file)
        tagged = [e for e in result.entries if e.status == TagStatus.TAGGED]
        assert len(tagged) == 2

    def test_existing_meta_is_preserved(self, env_file, meta_file):
        _write(meta_file, json.dumps({"DEBUG": ["existing"]}))
        tag_keys(env_file, {"API_KEY": ["new"]}, meta_path=meta_file)
        data = json.loads(Path(meta_file).read_text())
        assert "existing" in data["DEBUG"]
        assert "new" in data["API_KEY"]


# ---------------------------------------------------------------------------
# keys_for_tag
# ---------------------------------------------------------------------------

class TestKeysForTag:
    def test_returns_matching_keys(self, env_file, meta_file):
        tag_keys(env_file, {"DB_PASSWORD": ["secret"], "API_KEY": ["secret"]}, meta_path=meta_file)
        keys = keys_for_tag(meta_file, "secret")
        assert set(keys) == {"DB_PASSWORD", "API_KEY"}

    def test_returns_empty_for_unknown_tag(self, env_file, meta_file):
        tag_keys(env_file, {"DEBUG": ["flag"]}, meta_path=meta_file)
        keys = keys_for_tag(meta_file, "nonexistent")
        assert keys == []
