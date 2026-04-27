"""Tests for envoy.scope."""
from __future__ import annotations

import os
import tempfile
import pytest

from envoy.scope import (
    ScopeResult,
    filter_by_keys,
    filter_by_pattern,
    filter_by_prefix,
)

SAMPLE: dict[str, str] = {
    "APP_HOST": "localhost",
    "APP_PORT": "8080",
    "DB_HOST": "db.local",
    "DB_PASSWORD": "secret",
    "LOG_LEVEL": "debug",
}


class TestFilterByPrefix:
    def test_matches_prefix(self):
        result = filter_by_prefix(SAMPLE, "APP_")
        assert set(result.matched) == {"APP_HOST", "APP_PORT"}

    def test_excluded_contains_rest(self):
        result = filter_by_prefix(SAMPLE, "APP_")
        assert "DB_HOST" in result.excluded
        assert "LOG_LEVEL" in result.excluded

    def test_strip_prefix(self):
        result = filter_by_prefix(SAMPLE, "APP_", strip_prefix=True)
        assert "HOST" in result.matched
        assert "PORT" in result.matched

    def test_no_match_gives_empty_matched(self):
        result = filter_by_prefix(SAMPLE, "MISSING_")
        assert result.matched == {}
        assert len(result.excluded) == len(SAMPLE)

    def test_scope_name_defaults_to_prefix(self):
        result = filter_by_prefix(SAMPLE, "APP_")
        assert result.scope_name == "APP_"

    def test_custom_scope_name(self):
        result = filter_by_prefix(SAMPLE, "APP_", scope_name="application")
        assert result.scope_name == "application"


class TestFilterByPattern:
    def test_matches_regex(self):
        result = filter_by_pattern(SAMPLE, r"^DB_")
        assert set(result.matched) == {"DB_HOST", "DB_PASSWORD"}

    def test_partial_pattern(self):
        result = filter_by_pattern(SAMPLE, r"HOST")
        assert "APP_HOST" in result.matched
        assert "DB_HOST" in result.matched

    def test_no_match(self):
        result = filter_by_pattern(SAMPLE, r"^NOPE")
        assert result.matched == {}

    def test_scope_name_defaults_to_pattern(self):
        result = filter_by_pattern(SAMPLE, r"^DB_")
        assert result.scope_name == r"^DB_"


class TestFilterByKeys:
    def test_explicit_keys(self):
        result = filter_by_keys(SAMPLE, ["LOG_LEVEL", "APP_PORT"])
        assert set(result.matched) == {"LOG_LEVEL", "APP_PORT"}

    def test_missing_keys_not_in_matched(self):
        result = filter_by_keys(SAMPLE, ["DOES_NOT_EXIST"])
        assert result.matched == {}

    def test_excluded_has_remaining(self):
        result = filter_by_keys(SAMPLE, ["LOG_LEVEL"])
        assert "APP_HOST" in result.excluded

    def test_scope_name_default(self):
        result = filter_by_keys(SAMPLE, ["LOG_LEVEL"])
        assert result.scope_name == "explicit"


class TestScopeResult:
    def test_total(self):
        result = filter_by_prefix(SAMPLE, "APP_")
        assert result.total == len(SAMPLE)

    def test_summary_contains_scope_name(self):
        result = filter_by_prefix(SAMPLE, "APP_", scope_name="myapp")
        assert "myapp" in result.summary()

    def test_summary_contains_counts(self):
        result = filter_by_prefix(SAMPLE, "APP_")
        assert "2 matched" in result.summary()
        assert "3 excluded" in result.summary()
