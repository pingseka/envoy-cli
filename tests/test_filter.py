"""Tests for envoy.filter."""
import pytest

from envoy.filter import filter_env, FilterResult


SAMPLE = {
    "APP_NAME": "myapp",
    "APP_PORT": "8080",
    "DB_HOST": "localhost",
    "DB_PASSWORD": "s3cr3t",
    "SECRET_KEY": "abc123",
    "DEBUG": "true",
}


class TestFilterResult:
    def test_total_counts_all_keys(self):
        r = FilterResult(matched={"A": "1"}, excluded={"B": "2", "C": "3"})
        assert r.total == 3

    def test_matched_count(self):
        r = FilterResult(matched={"A": "1", "B": "2"}, excluded={})
        assert r.matched_count == 2

    def test_summary_string(self):
        r = FilterResult(matched={"A": "1"}, excluded={"B": "2"})
        assert "1 matched" in r.summary()
        assert "1 excluded" in r.summary()
        assert "total 2" in r.summary()


class TestFilterByKeyPattern:
    def test_matches_prefix(self):
        result = filter_env(SAMPLE, key_pattern=r"^APP_")
        assert set(result.matched.keys()) == {"APP_NAME", "APP_PORT"}

    def test_no_match_gives_empty_matched(self):
        result = filter_env(SAMPLE, key_pattern=r"^NONEXISTENT")
        assert result.matched == {}
        assert len(result.excluded) == len(SAMPLE)

    def test_partial_key_pattern(self):
        result = filter_env(SAMPLE, key_pattern=r"HOST")
        assert "DB_HOST" in result.matched


class TestFilterByValuePattern:
    def test_matches_numeric_values(self):
        result = filter_env(SAMPLE, value_pattern=r"^\d+$")
        assert "APP_PORT" in result.matched
        assert "APP_NAME" not in result.matched

    def test_value_pattern_case_sensitive(self):
        result = filter_env(SAMPLE, value_pattern=r"true")
        assert "DEBUG" in result.matched


class TestFilterSecretsOnly:
    def test_secrets_only_returns_secret_keys(self):
        result = filter_env(SAMPLE, secrets_only=True)
        for k in result.matched:
            assert any(kw in k.upper() for kw in ("SECRET", "PASSWORD", "TOKEN", "KEY"))

    def test_non_secrets_only_excludes_secrets(self):
        result = filter_env(SAMPLE, non_secrets_only=True)
        for k in result.matched:
            assert k not in ("DB_PASSWORD", "SECRET_KEY")

    def test_mutually_exclusive_raises(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            filter_env(SAMPLE, secrets_only=True, non_secrets_only=True)


class TestFilterByKeys:
    def test_explicit_key_list(self):
        result = filter_env(SAMPLE, keys=["APP_NAME", "DEBUG"])
        assert set(result.matched.keys()) == {"APP_NAME", "DEBUG"}

    def test_key_not_in_env_is_simply_absent(self):
        result = filter_env(SAMPLE, keys=["MISSING_KEY"])
        assert result.matched == {}


class TestCombinedFilters:
    def test_key_and_value_pattern_combined(self):
        result = filter_env(SAMPLE, key_pattern=r"^APP_", value_pattern=r"\d+")
        assert set(result.matched.keys()) == {"APP_PORT"}

    def test_empty_env_returns_empty_result(self):
        result = filter_env({})
        assert result.matched == {}
        assert result.excluded == {}
