"""Tests for envoy.template module."""

import pytest
from envoy.template import (
    render_env,
    RenderResult,
    RenderIssue,
    _find_variables,
    _substitute,
)


class TestFindVariables:
    def test_curly_brace_syntax(self):
        assert _find_variables("${FOO}") == ["FOO"]

    def test_dollar_syntax(self):
        assert _find_variables("$BAR") == ["BAR"]

    def test_multiple_vars(self):
        result = _find_variables("${HOST}:${PORT}")
        assert result == ["HOST", "PORT"]

    def test_no_vars(self):
        assert _find_variables("plain_value") == []

    def test_mixed_syntax(self):
        result = _find_variables("$USER@${HOST}")
        assert "USER" in result
        assert "HOST" in result


class TestSubstitute:
    def test_replaces_curly_brace(self):
        assert _substitute("${FOO}", {"FOO": "bar"}) == "bar"

    def test_replaces_dollar_syntax(self):
        assert _substitute("$FOO", {"FOO": "bar"}) == "bar"

    def test_leaves_unknown_unchanged(self):
        assert _substitute("${UNKNOWN}", {}) == "${UNKNOWN}"

    def test_partial_substitution(self):
        result = _substitute("${A}-${B}", {"A": "hello"})
        assert result == "hello-${B}"


class TestRenderEnv:
    def test_simple_substitution(self):
        env = {"BASE": "http://localhost", "URL": "${BASE}/api"}
        result = render_env(env)
        assert result.rendered["URL"] == "http://localhost/api"
        assert not result.has_issues

    def test_self_referencing_env(self):
        env = {"HOST": "example.com", "DB": "postgres://${HOST}/mydb"}
        result = render_env(env)
        assert result.rendered["DB"] == "postgres://example.com/mydb"

    def test_external_context(self):
        env = {"GREETING": "Hello, ${NAME}!"}
        result = render_env(env, context={"NAME": "World"})
        assert result.rendered["GREETING"] == "Hello, World!"
        assert not result.has_issues

    def test_missing_variable_creates_issue(self):
        env = {"URL": "${MISSING_VAR}/path"}
        result = render_env(env)
        assert result.has_issues
        assert result.issues[0].variable == "MISSING_VAR"
        assert result.issues[0].key == "URL"

    def test_no_vars_passes_through(self):
        env = {"PLAIN": "just_a_value", "NUM": "42"}
        result = render_env(env)
        assert result.rendered == env
        assert not result.has_issues

    def test_context_overrides_env(self):
        env = {"HOST": "localhost", "URL": "${HOST}:8080"}
        result = render_env(env, context={"HOST": "prod.example.com"})
        assert result.rendered["URL"] == "prod.example.com:8080"

    def test_render_result_issue_str(self):
        issue = RenderIssue(key="URL", variable="HOST", message="undefined variable")
        assert "URL" in str(issue)
        assert "HOST" in str(issue)
        assert "undefined variable" in str(issue)

    def test_multiple_issues(self):
        env = {"A": "${X}", "B": "${Y}"}
        result = render_env(env)
        assert len(result.issues) == 2
        variables = {i.variable for i in result.issues}
        assert variables == {"X", "Y"}
