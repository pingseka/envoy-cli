"""Tests for envoy.diff module."""

import os
import tempfile
import pytest

from envoy.diff import diff_env_files, DiffStatus, DiffEntry


def write_temp_env(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".env")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.fixture(autouse=True)
def cleanup(tmp_files):
    yield
    for path in tmp_files:
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def tmp_files():
    return []


def make_envs(base_content, target_content):
    base = write_temp_env(base_content)
    target = write_temp_env(target_content)
    return base, target


class TestDiffEnvFiles:
    def test_added_key(self):
        base, target = make_envs("FOO=bar\n", "FOO=bar\nBAZ=qux\n")
        result = diff_env_files(base, target)
        assert result.has_changes
        added = [e for e in result.entries if e.status == DiffStatus.ADDED]
        assert len(added) == 1
        assert added[0].key == "BAZ"
        assert added[0].new_value == "qux"

    def test_removed_key(self):
        base, target = make_envs("FOO=bar\nBAZ=qux\n", "FOO=bar\n")
        result = diff_env_files(base, target)
        removed = [e for e in result.entries if e.status == DiffStatus.REMOVED]
        assert len(removed) == 1
        assert removed[0].key == "BAZ"
        assert removed[0].old_value == "qux"

    def test_changed_key(self):
        base, target = make_envs("FOO=bar\n", "FOO=baz\n")
        result = diff_env_files(base, target)
        changed = [e for e in result.entries if e.status == DiffStatus.CHANGED]
        assert len(changed) == 1
        assert changed[0].old_value == "bar"
        assert changed[0].new_value == "baz"

    def test_no_changes(self):
        base, target = make_envs("FOO=bar\n", "FOO=bar\n")
        result = diff_env_files(base, target)
        assert not result.has_changes

    def test_show_unchanged(self):
        base, target = make_envs("FOO=bar\n", "FOO=bar\n")
        result = diff_env_files(base, target, show_unchanged=True)
        assert len(result.entries) == 1
        assert result.entries[0].status == DiffStatus.UNCHANGED

    def test_secret_key_masked_in_str(self):
        base, target = make_envs("SECRET_KEY=old\n", "SECRET_KEY=new\n")
        result = diff_env_files(base, target)
        entry = result.entries[0]
        assert entry.is_secret
        assert "****" in str(entry)
        assert "old" not in str(entry)
        assert "new" not in str(entry)

    def test_summary_counts(self):
        base, target = make_envs(
            "FOO=bar\nREMOVED=x\n",
            "FOO=changed\nADDED=y\n"
        )
        result = diff_env_files(base, target)
        summary = result.summary
        assert summary["added"] == 1
        assert summary["removed"] == 1
        assert summary["changed"] == 1

    def test_str_output_prefixes(self):
        base, target = make_envs("A=1\nB=2\n", "A=9\nC=3\n")
        result = diff_env_files(base, target)
        output = str(result)
        assert "- B=2" in output
        assert "+ C=3" in output
        assert "~ A: 1 -> 9" in output
