"""Tests for envoy.normalize."""

from __future__ import annotations

import os
import tempfile
import pytest

from envoy.normalize import normalize_env, NormalizeOp, NormalizeResult


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "db_host=localhost\nDB_PORT=5432\nSECRET=  myvalue  \nTOKEN='abc123'\n")
    return p


class TestNormalizeEnv:
    def test_key_upper_normalizes_lowercase(self, env_file):
        result = normalize_env(env_file, key_case="upper")
        assert "DB_HOST" in result.output
        assert "db_host" not in result.output

    def test_key_lower_normalizes_uppercase(self, env_file):
        result = normalize_env(env_file, key_case="lower")
        assert "db_port" in result.output
        assert "DB_PORT" not in result.output

    def test_no_key_case_leaves_keys_unchanged(self, env_file):
        result = normalize_env(env_file)
        assert "db_host" in result.output
        assert "DB_PORT" in result.output

    def test_strip_values_removes_whitespace(self, env_file):
        result = normalize_env(env_file, strip_values=True)
        assert result.output["SECRET"] == "myvalue"

    def test_strip_values_false_preserves_whitespace(self, env_file):
        result = normalize_env(env_file, strip_values=False)
        assert result.output["SECRET"] == "  myvalue  "

    def test_unquote_removes_single_quotes(self, env_file):
        result = normalize_env(env_file, unquote_values=True)
        assert result.output["TOKEN"] == "abc123"

    def test_unquote_false_preserves_quotes(self, env_file):
        result = normalize_env(env_file, unquote_values=False)
        assert result.output["TOKEN"] == "'abc123'"

    def test_changed_count_reflects_modifications(self, env_file):
        result = normalize_env(env_file, key_case="upper", strip_values=True)
        assert result.changed_count() >= 1

    def test_no_changes_when_already_normalized(self, tmp_dir):
        p = os.path.join(tmp_dir, "clean.env")
        _write(p, "KEY=value\nFOO=bar\n")
        result = normalize_env(p, key_case="upper")
        assert result.changed_count() == 0

    def test_ops_applied_recorded(self, env_file):
        result = normalize_env(env_file, key_case="upper")
        changed = result.changed()
        for entry in changed:
            assert NormalizeOp.KEY_UPPER in entry.ops_applied

    def test_summary_string(self, env_file):
        result = normalize_env(env_file, key_case="upper")
        s = result.summary()
        assert "normalized" in s

    def test_entry_str(self, env_file):
        result = normalize_env(env_file, key_case="upper")
        changed = result.changed()
        assert len(changed) > 0
        s = str(changed[0])
        assert "->" in s

    def test_file_not_found_raises(self, tmp_dir):
        with pytest.raises(FileNotFoundError):
            normalize_env(os.path.join(tmp_dir, "missing.env"))

    def test_combined_ops_all_applied(self, tmp_dir):
        p = os.path.join(tmp_dir, "combo.env")
        _write(p, "my_key=  'hello'  \n")
        result = normalize_env(p, key_case="upper", strip_values=True, unquote_values=True)
        assert "MY_KEY" in result.output
        assert result.output["MY_KEY"] == "'hello'"
