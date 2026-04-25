"""Unit tests for CompareEntry and CompareResult helpers."""
import pytest
from envoy.compare import CompareEntry, CompareResult, ChangeType


class TestCompareEntry:
    def test_display_base_returns_value(self):
        e = CompareEntry("FOO", ChangeType.MODIFIED, base_value="old", target_value="new")
        assert e.display_base() == "old"

    def test_display_target_returns_value(self):
        e = CompareEntry("FOO", ChangeType.MODIFIED, base_value="old", target_value="new")
        assert e.display_target() == "new"

    def test_secret_base_masked(self):
        e = CompareEntry("SECRET_KEY", ChangeType.MODIFIED,
                         base_value="s3cr3t", target_value="n3w", is_secret=True)
        assert e.display_base() == "***"

    def test_secret_target_masked(self):
        e = CompareEntry("SECRET_KEY", ChangeType.MODIFIED,
                         base_value="s3cr3t", target_value="n3w", is_secret=True)
        assert e.display_target() == "***"

    def test_none_base_returns_empty(self):
        e = CompareEntry("NEW", ChangeType.ADDED, target_value="v")
        assert e.display_base() == ""

    def test_none_target_returns_empty(self):
        e = CompareEntry("OLD", ChangeType.REMOVED, base_value="v")
        assert e.display_target() == ""

    def test_str_added_starts_with_plus(self):
        e = CompareEntry("K", ChangeType.ADDED, target_value="v")
        assert str(e).startswith("+")

    def test_str_removed_starts_with_minus(self):
        e = CompareEntry("K", ChangeType.REMOVED, base_value="v")
        assert str(e).startswith("-")

    def test_str_modified_starts_with_tilde(self):
        e = CompareEntry("K", ChangeType.MODIFIED, base_value="a", target_value="b")
        assert str(e).startswith("~")


class TestCompareResult:
    def _make_result(self):
        return CompareResult(entries=[
            CompareEntry("A", ChangeType.ADDED, target_value="1"),
            CompareEntry("B", ChangeType.REMOVED, base_value="2"),
            CompareEntry("C", ChangeType.MODIFIED, base_value="3", target_value="4"),
            CompareEntry("D", ChangeType.UNCHANGED, base_value="5", target_value="5"),
        ])

    def test_added_property(self):
        r = self._make_result()
        assert len(r.added) == 1 and r.added[0].key == "A"

    def test_removed_property(self):
        r = self._make_result()
        assert len(r.removed) == 1 and r.removed[0].key == "B"

    def test_modified_property(self):
        r = self._make_result()
        assert len(r.modified) == 1 and r.modified[0].key == "C"

    def test_unchanged_property(self):
        r = self._make_result()
        assert len(r.unchanged) == 1 and r.unchanged[0].key == "D"

    def test_has_changes_true(self):
        r = self._make_result()
        assert r.has_changes is True

    def test_has_changes_false_when_only_unchanged(self):
        r = CompareResult(entries=[
            CompareEntry("X", ChangeType.UNCHANGED, base_value="v", target_value="v")
        ])
        assert r.has_changes is False

    def test_summary_contains_counts(self):
        r = self._make_result()
        s = r.summary()
        assert "+1" in s and "-1" in s and "~1" in s
