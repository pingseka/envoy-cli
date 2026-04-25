"""Tests for envoy.history module."""
import json
import pytest
from pathlib import Path
from envoy.history import HistoryEntry, HistoryLog


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "history.json"


@pytest.fixture
def history_log(log_path):
    log = HistoryLog(path=log_path)
    log.load()
    return log


class TestHistoryEntry:
    def test_to_dict_roundtrip(self):
        entry = HistoryEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="set",
            key="DB_URL",
            old_value=None,
            new_value="postgres://localhost/db",
            author="alice",
            note="initial setup",
        )
        restored = HistoryEntry.from_dict(entry.to_dict())
        assert restored.key == entry.key
        assert restored.action == entry.action
        assert restored.new_value == entry.new_value
        assert restored.author == entry.author

    def test_str_includes_action_and_key(self):
        entry = HistoryEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="delete",
            key="OLD_KEY",
            old_value="val",
            new_value=None,
        )
        s = str(entry)
        assert "DELETE" in s
        assert "OLD_KEY" in s

    def test_str_includes_author_when_present(self):
        entry = HistoryEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="set",
            key="X",
            old_value=None,
            new_value="1",
            author="bob",
        )
        assert "bob" in str(entry)

    def test_defaults_have_empty_author_and_note(self):
        d = {"timestamp": "t", "action": "set", "key": "K",
             "old_value": None, "new_value": "v"}
        entry = HistoryEntry.from_dict(d)
        assert entry.author == ""
        assert entry.note == ""


class TestHistoryLog:
    def test_record_appends_entry(self, history_log):
        history_log.record("set", "API_KEY", new_value="abc")
        assert len(history_log.entries) == 1
        assert history_log.entries[0].key == "API_KEY"

    def test_save_and_load_roundtrip(self, log_path):
        log = HistoryLog(path=log_path)
        log.load()
        log.record("set", "FOO", old_value=None, new_value="bar", author="ci")
        log.save()

        log2 = HistoryLog(path=log_path)
        log2.load()
        assert len(log2.entries) == 1
        assert log2.entries[0].author == "ci"

    def test_for_key_filters_correctly(self, history_log):
        history_log.record("set", "A", new_value="1")
        history_log.record("set", "B", new_value="2")
        history_log.record("set", "A", old_value="1", new_value="3")
        assert len(history_log.for_key("A")) == 2
        assert len(history_log.for_key("B")) == 1

    def test_recent_returns_last_n(self, history_log):
        for i in range(10):
            history_log.record("set", f"K{i}", new_value=str(i))
        assert len(history_log.recent(5)) == 5
        assert history_log.recent(5)[-1].key == "K9"

    def test_load_missing_file_is_empty(self, log_path):
        log = HistoryLog(path=log_path)
        log.load()
        assert log.entries == []

    def test_record_returns_entry(self, history_log):
        entry = history_log.record("import", "SECRET", new_value="x")
        assert isinstance(entry, HistoryEntry)
        assert entry.action == "import"
