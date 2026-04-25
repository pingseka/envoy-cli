"""Tests for envoy.lint module."""

import os
import tempfile
import pytest

from envoy.lint import lint_env_file, LintSeverity, LintIssue, LintResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(content: str) -> str:
    """Write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".env")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# LintResult unit tests
# ---------------------------------------------------------------------------

class TestLintResult:
    def test_empty_result_has_no_errors(self):
        r = LintResult()
        assert not r.has_errors()

    def test_error_issue_makes_has_errors_true(self):
        r = LintResult(issues=[
            LintIssue(1, "KEY", "bad", LintSeverity.ERROR)
        ])
        assert r.has_errors()

    def test_warning_does_not_make_has_errors_true(self):
        r = LintResult(issues=[
            LintIssue(1, "key", "style", LintSeverity.WARNING)
        ])
        assert not r.has_errors()

    def test_errors_filters_correctly(self):
        r = LintResult(issues=[
            LintIssue(1, "A", "e", LintSeverity.ERROR),
            LintIssue(2, "B", "w", LintSeverity.WARNING),
        ])
        assert len(r.errors()) == 1
        assert len(r.warnings()) == 1


# ---------------------------------------------------------------------------
# LintIssue.__str__
# ---------------------------------------------------------------------------

class TestLintIssueStr:
    def test_includes_severity(self):
        issue = LintIssue(3, "MY_KEY", "some problem", LintSeverity.WARNING)
        assert "WARNING" in str(issue)

    def test_includes_line_number(self):
        issue = LintIssue(7, None, "bad line", LintSeverity.ERROR)
        assert "7" in str(issue)

    def test_includes_key_when_present(self):
        issue = LintIssue(1, "SECRET", "msg", LintSeverity.ERROR)
        assert "SECRET" in str(issue)


# ---------------------------------------------------------------------------
# lint_env_file integration tests
# ---------------------------------------------------------------------------

class TestLintEnvFile:
    def test_clean_file_has_no_issues(self):
        path = _write("APP_NAME=myapp\nDEBUG=false\n")
        result = lint_env_file(path)
        assert result.issues == []

    def test_detects_lowercase_key(self):
        path = _write("app_name=myapp\n")
        result = lint_env_file(path)
        warnings = result.warnings()
        assert any("UPPER_SNAKE_CASE" in w.message for w in warnings)

    def test_detects_empty_value(self):
        path = _write("MY_KEY=\n")
        result = lint_env_file(path)
        assert any("empty" in i.message.lower() for i in result.warnings())

    def test_detects_duplicate_key(self):
        path = _write("FOO=1\nFOO=2\n")
        result = lint_env_file(path)
        assert any("Duplicate" in i.message for i in result.errors())

    def test_detects_invalid_line(self):
        path = _write("NOTAVALIDLINE\n")
        result = lint_env_file(path)
        assert result.has_errors()

    def test_skips_comments_and_blanks(self):
        path = _write("# comment\n\nFOO=bar\n")
        result = lint_env_file(path)
        assert result.issues == []

    def test_detects_key_with_spaces(self):
        path = _write("MY KEY=value\n")
        result = lint_env_file(path)
        assert any("spaces" in i.message for i in result.errors())
