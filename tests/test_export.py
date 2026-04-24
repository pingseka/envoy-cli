"""Tests for envoy.export module."""

import json
import os
import tempfile

import pytest

from envoy.export import export_env, export_to_file, SUPPORTED_FORMATS


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "SECRET_KEY": "s3cr3t",
    "DATABASE_PASSWORD": "hunter2",
    "PATH_WITH_SPACES": "hello world",
}


class TestExportEnv:
    def test_dotenv_format_basic(self):
        result = export_env({"FOO": "bar", "BAZ": "qux"}, fmt="dotenv")
        assert "FOO=bar" in result
        assert "BAZ=qux" in result

    def test_shell_format_has_export(self):
        result = export_env({"FOO": "bar"}, fmt="shell")
        assert result.strip() == "export FOO=bar"

    def test_json_format_is_valid_json(self):
        result = export_env({"FOO": "bar", "NUM": "42"}, fmt="json")
        parsed = json.loads(result)
        assert parsed == {"FOO": "bar", "NUM": "42"}

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            export_env({"FOO": "bar"}, fmt="xml")

    def test_mask_secrets_dotenv(self):
        result = export_env(SAMPLE_ENV, fmt="dotenv", mask_secrets=True)
        assert "s3cr3t" not in result
        assert "hunter2" not in result
        assert "SECRET_KEY=****" in result
        assert "DATABASE_PASSWORD=****" in result
        # Non-secret values should remain
        assert "APP_NAME=myapp" in result

    def test_mask_secrets_json(self):
        result = export_env(SAMPLE_ENV, fmt="json", mask_secrets=True)
        parsed = json.loads(result)
        assert parsed["SECRET_KEY"] == "****"
        assert parsed["DATABASE_PASSWORD"] == "****"
        assert parsed["APP_NAME"] == "myapp"

    def test_values_with_spaces_are_quoted(self):
        result = export_env({"MSG": "hello world"}, fmt="dotenv")
        assert 'MSG="hello world"' in result

    def test_shell_values_with_spaces_are_quoted(self):
        result = export_env({"MSG": "hello world"}, fmt="shell")
        assert 'export MSG="hello world"' in result

    def test_custom_mask_value(self):
        result = export_env(
            {"SECRET_KEY": "abc"}, fmt="dotenv", mask_secrets=True, mask_value="[REDACTED]"
        )
        assert "[REDACTED]" in result

    def test_empty_env_returns_empty_string(self):
        assert export_env({}, fmt="dotenv") == ""
        assert export_env({}, fmt="shell") == ""
        assert json.loads(export_env({}, fmt="json")) == {}


class TestExportToFile:
    def test_writes_dotenv_file(self, tmp_path):
        out = str(tmp_path / "out.env")
        export_to_file({"FOO": "bar"}, out, fmt="dotenv")
        content = open(out).read()
        assert "FOO=bar" in content

    def test_file_ends_with_newline(self, tmp_path):
        out = str(tmp_path / "out.env")
        export_to_file({"A": "1"}, out)
        content = open(out).read()
        assert content.endswith("\n")

    def test_writes_json_file(self, tmp_path):
        out = str(tmp_path / "out.json")
        export_to_file({"X": "y"}, out, fmt="json")
        parsed = json.loads(open(out).read())
        assert parsed == {"X": "y"}
