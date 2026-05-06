import os
import tempfile
import pytest

from envoy.truncate import (
    TruncateStatus,
    TruncateEntry,
    TruncateResult,
    truncate_env,
)


def _write(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def env_file(tmp_dir):
    p = os.path.join(tmp_dir, ".env")
    _write(p, "SHORT=hi\nLONG=abcdefghijklmnopqrstuvwxyz\nMED=hello_world\n")
    return p


class TestTruncateEnv:
    def test_truncates_long_value(self, env_file):
        result = truncate_env(env_file, max_length=10)
        entry = next(e for e in result.entries if e.key == "LONG")
        assert entry.status == TruncateStatus.TRUNCATED
        assert len(entry.result) == 10
        assert entry.result.endswith("...")

    def test_unchanged_when_short_enough(self, env_file):
        result = truncate_env(env_file, max_length=50)
        for entry in result.entries:
            assert entry.status == TruncateStatus.UNCHANGED

    def test_skips_keys_not_in_filter(self, env_file):
        result = truncate_env(env_file, max_length=5, keys=["SHORT"])
        skipped = [e for e in result.entries if e.status == TruncateStatus.SKIPPED]
        skipped_keys = {e.key for e in skipped}
        assert "LONG" in skipped_keys
        assert "MED" in skipped_keys

    def test_only_specified_keys_truncated(self, env_file):
        result = truncate_env(env_file, max_length=5, keys=["LONG"])
        entry = next(e for e in result.entries if e.key == "LONG")
        assert entry.status == TruncateStatus.TRUNCATED

    def test_custom_suffix(self, env_file):
        result = truncate_env(env_file, max_length=8, suffix="--")
        entry = next(e for e in result.entries if e.key == "LONG")
        assert entry.result.endswith("--")
        assert len(entry.result) == 8

    def test_summary_counts(self, env_file):
        result = truncate_env(env_file, max_length=10)
        assert "truncated" in result.summary()
        assert "unchanged" in result.summary()

    def test_to_dict_contains_all_keys(self, env_file):
        result = truncate_env(env_file, max_length=10)
        d = result.to_dict()
        assert "SHORT" in d
        assert "LONG" in d
        assert "MED" in d

    def test_to_dict_value_is_truncated(self, env_file):
        result = truncate_env(env_file, max_length=10)
        d = result.to_dict()
        assert len(d["LONG"]) == 10

    def test_invalid_max_length_raises(self, env_file):
        with pytest.raises(ValueError):
            truncate_env(env_file, max_length=2, suffix="...")

    def test_entry_str_truncated(self, env_file):
        result = truncate_env(env_file, max_length=10)
        entry = next(e for e in result.entries if e.key == "LONG")
        s = str(entry)
        assert "truncated" in s
        assert "LONG" in s

    def test_entry_str_unchanged(self, env_file):
        result = truncate_env(env_file, max_length=50)
        entry = next(e for e in result.entries if e.key == "SHORT")
        assert "unchanged" in str(entry)
