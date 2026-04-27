"""Tests for envoy.flatten."""
from __future__ import annotations

import os
import tempfile
import pytest

from envoy.flatten import flatten_env, FlattenStatus


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "APP_HOST=localhost\nAPP_PORT=5432\nDB_NAME=mydb\n")
    return p


class TestFlattenEnv:
    def test_all_kept_when_no_duplicates(self, env_file):
        result = flatten_env(env_file)
        assert len(result.kept()) == 3
        assert result.duplicates() == []

    def test_strip_prefix_renames_keys(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "APP_HOST=localhost\nAPP_PORT=8080\nOTHER=x\n")
        result = flatten_env(p, strip_prefix="APP_")
        keys = result.to_dict()
        assert "HOST" in keys
        assert "PORT" in keys
        assert "OTHER" in keys
        assert "APP_HOST" not in keys

    def test_renamed_entries_have_original_key(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "APP_HOST=localhost\n")
        result = flatten_env(p, strip_prefix="APP_")
        renamed = result.renamed()
        assert len(renamed) == 1
        assert renamed[0].original_key == "APP_HOST"
        assert renamed[0].key == "HOST"

    def test_duplicate_key_keep_first(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "KEY=first\nKEY=second\n")
        result = flatten_env(p, keep_first=True)
        assert result.to_dict()["KEY"] == "first"
        assert len(result.duplicates()) == 1

    def test_duplicate_key_keep_last(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "KEY=first\nKEY=second\n")
        result = flatten_env(p, keep_first=False)
        assert result.to_dict()["KEY"] == "second"

    def test_to_dict_excludes_duplicates(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "A=1\nA=2\nB=3\n")
        result = flatten_env(p)
        d = result.to_dict()
        assert list(d.keys()).count("A") == 1
        assert "B" in d

    def test_summary_string(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "APP_X=1\nAPP_Y=2\nZ=3\n")
        result = flatten_env(p, strip_prefix="APP_")
        s = result.summary()
        assert "kept" in s
        assert "renamed" in s

    def test_file_not_found_raises(self, tmp_dir):
        with pytest.raises(FileNotFoundError):
            flatten_env(os.path.join(tmp_dir, "missing.env"))

    def test_empty_file_gives_empty_result(self, tmp_dir):
        p = os.path.join(tmp_dir, ".env")
        _write(p, "")
        result = flatten_env(p)
        assert result.to_dict() == {}
        assert result.summary() == "0 kept, 0 duplicates removed, 0 renamed"
