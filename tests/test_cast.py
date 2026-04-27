"""Tests for envoy.cast module."""
from __future__ import annotations

import pytest

from envoy.cast import CastType, CastEntry, CastResult, cast_env, _cast_value


class TestCastValue:
    def test_string_passthrough(self):
        assert _cast_value("hello", CastType.STRING) == "hello"

    def test_integer_conversion(self):
        assert _cast_value("42", CastType.INTEGER) == 42

    def test_float_conversion(self):
        assert abs(_cast_value("3.14", CastType.FLOAT) - 3.14) < 1e-9

    def test_boolean_true_variants(self):
        for val in ("true", "1", "yes", "on", "True", "YES"):
            assert _cast_value(val, CastType.BOOLEAN) is True

    def test_boolean_false_variants(self):
        for val in ("false", "0", "no", "off", "False", "NO"):
            assert _cast_value(val, CastType.BOOLEAN) is False

    def test_boolean_invalid_raises(self):
        with pytest.raises(ValueError):
            _cast_value("maybe", CastType.BOOLEAN)

    def test_list_splits_by_comma(self):
        assert _cast_value("a,b,c", CastType.LIST) == ["a", "b", "c"]

    def test_list_strips_whitespace(self):
        assert _cast_value(" a , b , c ", CastType.LIST) == ["a", "b", "c"]

    def test_list_empty_string_returns_empty(self):
        assert _cast_value("", CastType.LIST) == []

    def test_integer_invalid_raises(self):
        with pytest.raises(ValueError):
            _cast_value("not_a_number", CastType.INTEGER)


class TestCastEnv:
    def test_casts_all_keys(self):
        env = {"PORT": "8080", "DEBUG": "true", "NAME": "app"}
        schema = {
            "PORT": CastType.INTEGER,
            "DEBUG": CastType.BOOLEAN,
            "NAME": CastType.STRING,
        }
        result = cast_env(env, schema)
        assert len(result.entries) == 3
        assert result.values == {"PORT": 8080, "DEBUG": True, "NAME": "app"}

    def test_missing_key_casts_empty_string(self):
        result = cast_env({}, {"PORT": CastType.INTEGER})
        assert result.entries[0].ok is False

    def test_has_errors_false_when_all_ok(self):
        result = cast_env({"X": "1"}, {"X": CastType.INTEGER})
        assert result.has_errors is False

    def test_has_errors_true_when_any_fail(self):
        result = cast_env({"X": "bad"}, {"X": CastType.INTEGER})
        assert result.has_errors is True

    def test_errors_returns_only_failed_entries(self):
        env = {"A": "1", "B": "bad"}
        schema = {"A": CastType.INTEGER, "B": CastType.INTEGER}
        result = cast_env(env, schema)
        errs = result.errors()
        assert len(errs) == 1
        assert errs[0].key == "B"

    def test_values_excludes_failed(self):
        env = {"A": "1", "B": "bad"}
        schema = {"A": CastType.INTEGER, "B": CastType.INTEGER}
        result = cast_env(env, schema)
        assert "A" in result.values
        assert "B" not in result.values


class TestCastEntryStr:
    def test_ok_entry_str(self):
        entry = CastEntry(key="PORT", raw="8080", cast_type=CastType.INTEGER, value=8080, ok=True)
        assert "PORT" in str(entry)
        assert "integer" in str(entry)

    def test_error_entry_str_includes_error(self):
        entry = CastEntry(key="X", raw="bad", cast_type=CastType.INTEGER, value=None, ok=False, error="invalid")
        assert "ERROR" in str(entry)
        assert "invalid" in str(entry)
