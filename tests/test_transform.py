"""Unit tests for envoy.transform."""
from __future__ import annotations

import os
import tempfile

import pytest

from envoy.transform import TransformStatus, transform_env


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    path = os.path.join(tmp_dir, ".env")
    _write(path, "NAME=hello\nSECRET=World\nPORT=8080\n")
    return path


class TestTransformEnv:
    def test_upper_changes_lowercase_values(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        assert result.env["NAME"] == "HELLO"
        assert result.env["SECRET"] == "WORLD"

    def test_unchanged_when_already_upper(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        port_entry = next(e for e in result.entries if e.key == "PORT")
        assert port_entry.status == TransformStatus.UNCHANGED

    def test_none_return_leaves_value_unchanged(self, env_file):
        result = transform_env(env_file, lambda k, v: None)
        assert all(e.status == TransformStatus.UNCHANGED for e in result.entries)

    def test_keys_filter_limits_scope(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper(), keys=["NAME"])
        assert result.env["NAME"] == "HELLO"
        assert result.env["SECRET"] == "World"  # untouched

    def test_skipped_entries_recorded(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper(), keys=["NAME"])
        skipped = [e for e in result.entries if e.status == TransformStatus.SKIPPED]
        assert {e.key for e in skipped} == {"SECRET", "PORT"}

    def test_summary_reflects_changed_count(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        # NAME and SECRET change; PORT is already upper
        assert result.summary().startswith("2/3")

    def test_prefix_prepends_to_value(self, env_file):
        result = transform_env(env_file, lambda k, v: f"pre_{v}")
        assert result.env["NAME"] == "pre_hello"

    def test_suffix_appends_to_value(self, env_file):
        result = transform_env(env_file, lambda k, v: f"{v}_suf")
        assert result.env["PORT"] == "8080_suf"

    def test_changed_list_only_contains_changed(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        changed_keys = {e.key for e in result.changed()}
        assert "NAME" in changed_keys
        assert "PORT" not in changed_keys

    def test_str_representation_for_changed_entry(self, env_file):
        result = transform_env(env_file, lambda k, v: v.upper())
        entry = next(e for e in result.changed() if e.key == "NAME")
        assert "->" in str(entry)
