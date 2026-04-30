"""Tests for envoy.search."""
from __future__ import annotations

import pytest

from envoy.search import SearchMatch, SearchResult, search_env


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DATABASE_URL": "postgres://localhost/db",
    "SECRET_KEY": "supersecret",
    "DEBUG": "true",
    "PORT": "8080",
}


class TestSearchEnv:
    def test_key_pattern_matches(self):
        result = search_env(SAMPLE_ENV, key_pattern="^APP")
        assert result.match_count == 1
        assert result.matches[0].key == "APP_NAME"

    def test_value_pattern_matches(self):
        result = search_env(SAMPLE_ENV, value_pattern="postgres")
        assert result.match_count == 1
        assert result.matches[0].key == "DATABASE_URL"

    def test_both_patterns_must_match(self):
        result = search_env(SAMPLE_ENV, key_pattern="SECRET", value_pattern="super")
        assert result.match_count == 1
        assert result.matches[0].key == "SECRET_KEY"

    def test_no_match_returns_empty(self):
        result = search_env(SAMPLE_ENV, key_pattern="NONEXISTENT")
        assert result.match_count == 0
        assert result.matches == []

    def test_total_scanned_is_full_env(self):
        result = search_env(SAMPLE_ENV, key_pattern="PORT")
        assert result.total_scanned == len(SAMPLE_ENV)

    def test_case_insensitive_by_default(self):
        result = search_env(SAMPLE_ENV, key_pattern="app_name")
        assert result.match_count == 1

    def test_case_sensitive_no_match(self):
        result = search_env(SAMPLE_ENV, key_pattern="app_name", case_sensitive=True)
        assert result.match_count == 0

    def test_raises_if_no_pattern_given(self):
        with pytest.raises(ValueError):
            search_env(SAMPLE_ENV)

    def test_secret_key_is_flagged(self):
        result = search_env(SAMPLE_ENV, key_pattern="SECRET_KEY")
        assert result.matches[0].is_secret is True

    def test_non_secret_key_not_flagged(self):
        result = search_env(SAMPLE_ENV, key_pattern="^PORT$")
        assert result.matches[0].is_secret is False


class TestSearchMatch:
    def test_display_value_masks_secret(self):
        m = SearchMatch(key="SECRET_KEY", value="abc123", is_secret=True)
        assert m.display_value() == "***"

    def test_display_value_shows_plain(self):
        m = SearchMatch(key="PORT", value="8080", is_secret=False)
        assert m.display_value() == "8080"

    def test_str_uses_display_value(self):
        m = SearchMatch(key="SECRET_KEY", value="abc123", is_secret=True)
        assert str(m) == "SECRET_KEY=***"


class TestSearchResult:
    def test_summary_includes_counts(self):
        r = SearchResult(matches=[SearchMatch("A", "1")], total_scanned=5)
        assert "1 match" in r.summary()
        assert "5" in r.summary()

    def test_empty_summary(self):
        r = SearchResult(matches=[], total_scanned=3)
        assert "0 match" in r.summary()
