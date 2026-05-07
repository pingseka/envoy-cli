"""Tests for envoy.quote module."""

from __future__ import annotations

import os
import tempfile

import pytest

from envoy.quote import (
    QuoteStyle,
    QuoteStatus,
    QuoteResult,
    _apply_quote,
    quote_env,
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
    _write(p, "NAME=alice\nGREETING=hello world\nPASSWORD=secret\n")
    return p


# --- _apply_quote unit tests ---

class TestApplyQuote:
    def test_double_quote_plain(self):
        assert _apply_quote("hello", QuoteStyle.DOUBLE) == '"hello"'

    def test_single_quote_plain(self):
        assert _apply_quote("hello", QuoteStyle.SINGLE) == "'hello'"

    def test_none_strips_double_quotes(self):
        assert _apply_quote('"hello"', QuoteStyle.NONE) == "hello"

    def test_none_strips_single_quotes(self):
        assert _apply_quote("'hello'", QuoteStyle.NONE) == "hello"

    def test_none_leaves_unquoted_unchanged(self):
        assert _apply_quote("hello", QuoteStyle.NONE) == "hello"

    def test_double_escapes_inner_double_quote(self):
        result = _apply_quote('say "hi"', QuoteStyle.DOUBLE)
        assert result == '"say \\"hi\\""'

    def test_single_escapes_inner_single_quote(self):
        result = _apply_quote("it's", QuoteStyle.SINGLE)
        assert result == "'it\\'s'"


# --- quote_env integration tests ---

class TestQuoteEnv:
    def test_all_keys_quoted_by_default(self, env_file):
        result = quote_env(env_file, style=QuoteStyle.DOUBLE)
        assert all(
            e.status in (QuoteStatus.QUOTED, QuoteStatus.SKIPPED)
            for e in result.entries
        )

    def test_quoted_values_have_double_quotes(self, env_file):
        result = quote_env(env_file, style=QuoteStyle.DOUBLE)
        for key, val in result.env.items():
            assert val.startswith('"') and val.endswith('"'), f"{key}={val!r}"

    def test_only_specified_keys_changed(self, env_file):
        result = quote_env(env_file, style=QuoteStyle.DOUBLE, keys=["NAME"])
        skipped = [e.key for e in result.skipped()]
        assert "GREETING" in skipped
        assert "PASSWORD" in skipped
        changed = [e.key for e in result.changed()]
        assert "NAME" in changed

    def test_none_style_strips_quotes(self, tmp_dir):
        p = os.path.join(tmp_dir, "quoted.env")
        _write(p, 'KEY="value"\nOTHER=\'hello\'\n')
        result = quote_env(p, style=QuoteStyle.NONE)
        assert result.env["KEY"] == "value"
        assert result.env["OTHER"] == "hello"

    def test_already_correct_is_skipped(self, tmp_dir):
        p = os.path.join(tmp_dir, "pre.env")
        _write(p, 'NAME="alice"\n')
        result = quote_env(p, style=QuoteStyle.DOUBLE)
        assert result.entries[0].status == QuoteStatus.SKIPPED

    def test_summary_string(self, env_file):
        result = quote_env(env_file, style=QuoteStyle.DOUBLE)
        s = result.summary()
        assert "requoted" in s
        assert "skipped" in s

    def test_file_not_found_raises(self, tmp_dir):
        with pytest.raises(FileNotFoundError):
            quote_env(os.path.join(tmp_dir, "missing.env"))

    def test_single_style_produces_single_quotes(self, env_file):
        result = quote_env(env_file, style=QuoteStyle.SINGLE)
        for val in result.env.values():
            assert val.startswith("'") and val.endswith("'")
