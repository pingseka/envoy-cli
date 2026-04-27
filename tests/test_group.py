"""Tests for envoy.group module."""
from __future__ import annotations

import pytest
from envoy.group import group_by_prefix, group_by_pattern, GroupResult


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "CACHE_URL": "redis://localhost",
    "CACHE_TTL": "300",
    "APP_NAME": "envoy",
    "DEBUG": "true",
}


class TestGroupResult:
    def test_total_counts_all_keys(self):
        r = GroupResult(groups={"A": {"X": "1"}}, ungrouped={"Y": "2", "Z": "3"})
        assert r.total() == 3

    def test_summary_includes_group_names(self):
        r = GroupResult(groups={"DB_": {"DB_HOST": "h"}}, ungrouped={})
        assert "DB_" in r.summary()

    def test_summary_includes_ungrouped(self):
        r = GroupResult(groups={}, ungrouped={"X": "1"})
        assert "ungrouped" in r.summary()

    def test_empty_result_summary(self):
        r = GroupResult()
        assert r.summary() == "no keys"


class TestGroupByPrefix:
    def test_groups_db_keys(self):
        result = group_by_prefix(SAMPLE_ENV, ["DB_"])
        assert "DB_HOST" in result.groups["DB_"]
        assert "DB_PORT" in result.groups["DB_"]

    def test_ungrouped_contains_rest(self):
        result = group_by_prefix(SAMPLE_ENV, ["DB_"])
        assert "CACHE_URL" in result.ungrouped
        assert "APP_NAME" in result.ungrouped

    def test_multiple_prefixes(self):
        result = group_by_prefix(SAMPLE_ENV, ["DB_", "CACHE_"])
        assert len(result.groups["DB_"]) == 2
        assert len(result.groups["CACHE_"]) == 2
        assert set(result.ungrouped.keys()) == {"APP_NAME", "DEBUG"}

    def test_strip_prefix_removes_prefix_from_keys(self):
        result = group_by_prefix(SAMPLE_ENV, ["DB_"], strip_prefix=True)
        assert "HOST" in result.groups["DB_"]
        assert "PORT" in result.groups["DB_"]

    def test_no_match_gives_empty_group(self):
        result = group_by_prefix(SAMPLE_ENV, ["NOPE_"])
        assert result.groups["NOPE_"] == {}
        assert len(result.ungrouped) == len(SAMPLE_ENV)

    def test_empty_env_gives_empty_groups(self):
        result = group_by_prefix({}, ["DB_"])
        assert result.groups["DB_"] == {}
        assert result.ungrouped == {}


class TestGroupByPattern:
    def test_groups_by_regex(self):
        result = group_by_pattern(SAMPLE_ENV, {"database": r"^DB_", "cache": r"^CACHE_"})
        assert "DB_HOST" in result.groups["database"]
        assert "CACHE_URL" in result.groups["cache"]

    def test_ungrouped_has_unmatched_keys(self):
        result = group_by_pattern(SAMPLE_ENV, {"database": r"^DB_"})
        assert "APP_NAME" in result.ungrouped

    def test_partial_match_pattern(self):
        result = group_by_pattern(SAMPLE_ENV, {"ports": r"PORT"})
        assert "DB_PORT" in result.groups["ports"]

    def test_empty_pattern_dict_puts_all_in_ungrouped(self):
        result = group_by_pattern(SAMPLE_ENV, {})
        assert result.ungrouped == SAMPLE_ENV
        assert result.groups == {}
