"""Tests for envoy.interpolate."""
from __future__ import annotations

import pytest

from envoy.interpolate import (
    InterpolateStatus,
    interpolate_env,
)


class TestInterpolateEnv:
    def test_unchanged_when_no_references(self):
        env = {"FOO": "bar", "BAZ": "qux"}
        result = interpolate_env(env)
        assert all(e.status == InterpolateStatus.UNCHANGED for e in result.entries)

    def test_resolves_dollar_brace_syntax(self):
        env = {"BASE": "hello", "GREETING": "${BASE} world"}
        result = interpolate_env(env)
        entry = next(e for e in result.entries if e.key == "GREETING")
        assert entry.status == InterpolateStatus.RESOLVED
        assert entry.result == "hello world"

    def test_resolves_dollar_syntax(self):
        env = {"HOST": "localhost", "URL": "http://$HOST:8080"}
        result = interpolate_env(env)
        entry = next(e for e in result.entries if e.key == "URL")
        assert entry.status == InterpolateStatus.RESOLVED
        assert entry.result == "http://localhost:8080"

    def test_unresolved_when_reference_missing(self):
        env = {"URL": "http://${MISSING_HOST}:8080"}
        result = interpolate_env(env)
        entry = result.entries[0]
        assert entry.status == InterpolateStatus.UNRESOLVED
        assert "MISSING_HOST" in entry.missing
        assert entry.result == "http://${MISSING_HOST}:8080"

    def test_context_overrides_env_lookup(self):
        env = {"URL": "http://${HOST}"}
        context = {"HOST": "example.com"}
        result = interpolate_env(env, context)
        entry = result.entries[0]
        assert entry.status == InterpolateStatus.RESOLVED
        assert entry.result == "http://example.com"

    def test_multiple_references_in_one_value(self):
        env = {"PROTO": "https", "HOST": "api.dev", "URL": "${PROTO}://${HOST}/v1"}
        result = interpolate_env(env)
        entry = next(e for e in result.entries if e.key == "URL")
        assert entry.result == "https://api.dev/v1"
        assert entry.status == InterpolateStatus.RESOLVED

    def test_partial_resolution_marks_unresolved(self):
        env = {"PROTO": "https", "URL": "${PROTO}://${MISSING}"}
        result = interpolate_env(env)
        entry = next(e for e in result.entries if e.key == "URL")
        assert entry.status == InterpolateStatus.UNRESOLVED
        assert "MISSING" in entry.missing
        assert entry.result == "https://${MISSING}"

    def test_to_dict_returns_resolved_values(self):
        env = {"BASE": "world", "GREET": "hello ${BASE}"}
        result = interpolate_env(env)
        d = result.to_dict()
        assert d["GREET"] == "hello world"
        assert d["BASE"] == "world"

    def test_summary_counts_resolved_and_unresolved(self):
        env = {"A": "${EXISTS}", "EXISTS": "yes", "B": "${NOPE}"}
        result = interpolate_env(env)
        summary = result.summary()
        assert "resolved" in summary
        assert "unresolved" in summary

    def test_empty_env_returns_empty_result(self):
        result = interpolate_env({})
        assert result.entries == []
        assert result.summary() == "0 resolved, 0 unresolved"
