"""Tests for envoy.validate module."""
import pytest
from envoy.validate import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    validate_env,
)


class TestValidationResult:
    def test_empty_result_is_valid(self):
        result = ValidationResult()
        assert result.is_valid
        assert not result.has_errors
        assert not result.has_warnings
        assert len(result) == 0

    def test_error_makes_invalid(self):
        issue = ValidationIssue("KEY", "bad", ValidationSeverity.ERROR)
        result = ValidationResult(issues=[issue])
        assert not result.is_valid
        assert result.has_errors

    def test_warning_does_not_make_invalid(self):
        issue = ValidationIssue("KEY", "meh", ValidationSeverity.WARNING)
        result = ValidationResult(issues=[issue])
        assert result.is_valid
        assert result.has_warnings
        assert not result.has_errors


class TestValidationIssueStr:
    def test_str_includes_severity_and_key(self):
        issue = ValidationIssue("MY_KEY", "something wrong", ValidationSeverity.ERROR)
        s = str(issue)
        assert "ERROR" in s
        assert "MY_KEY" in s
        assert "something wrong" in s


class TestValidateEnv:
    def test_valid_env_no_issues(self):
        env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "8080"}
        result = validate_env(env)
        assert result.is_valid
        assert len(result) == 0

    def test_lowercase_key_warns(self):
        env = {"database_url": "value"}
        result = validate_env(env)
        warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert any("database_url" in i.key for i in warnings)

    def test_mixed_case_key_warns(self):
        env = {"MyKey": "value"}
        result = validate_env(env)
        assert any(i.key == "MyKey" for i in result.issues)

    def test_empty_value_warns_by_default(self):
        env = {"EMPTY_KEY": ""}
        result = validate_env(env)
        issues = [i for i in result.issues if i.key == "EMPTY_KEY"]
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING

    def test_empty_value_errors_when_disallowed(self):
        env = {"EMPTY_KEY": ""}
        result = validate_env(env, disallow_empty_values=True)
        issues = [i for i in result.issues if i.key == "EMPTY_KEY"]
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        assert not result.is_valid

    def test_required_key_missing_is_error(self):
        env = {"PORT": "8080"}
        result = validate_env(env, required_keys=["DATABASE_URL", "PORT"])
        errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert any("DATABASE_URL" in i.key for i in errors)
        assert not any("PORT" in i.key for i in errors)

    def test_required_key_present_no_error(self):
        env = {"DATABASE_URL": "postgres://localhost", "PORT": "5432"}
        result = validate_env(env, required_keys=["DATABASE_URL", "PORT"])
        assert result.is_valid

    def test_multiple_issues_accumulated(self):
        env = {"bad_key": "", "GOOD_KEY": "value"}
        result = validate_env(env, required_keys=["MISSING"], disallow_empty_values=True)
        assert len(result) >= 3  # bad_key naming + empty value error + missing key
