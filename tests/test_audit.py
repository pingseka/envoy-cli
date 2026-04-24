"""Tests for envoy.audit module."""

import json
import pytest
from pathlib import Path

from envoy.audit import AuditEntry, AuditLog


@pytest.fixture
def log_path(tmp_path) -> Path:
    return tmp_path / "audit.json"


@pytest.fixture
def audit_log(log_path) -> AuditLog:
    return AuditLog(log_path)


class TestAuditEntry:
    def test_to_dict_roundtrip(self):
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="sync",
            source=".env.dev",
            target=".env.prod",
            keys_affected=["DB_URL", "SECRET_KEY"],
            note="forced",
        )
        restored = AuditEntry.from_dict(entry.to_dict())
        assert restored.action == entry.action
        assert restored.keys_affected == entry.keys_affected
        assert restored.note == entry.note

    def test_str_includes_action(self):
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="diff",
            source=".env.a",
            target=None,
        )
        result = str(entry)
        assert "DIFF" in result
        assert ".env.a" in result

    def test_str_omits_missing_fields(self):
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            action="export",
            source=None,
            target=None,
        )
        result = str(entry)
        assert "src=" not in result
        assert "tgt=" not in result


class TestAuditLog:
    def test_record_creates_entry(self, audit_log):
        entry = audit_log.record("sync", source=".env.dev", target=".env.prod")
        assert entry.action == "sync"
        assert len(audit_log.entries()) == 1

    def test_record_persists_to_disk(self, audit_log, log_path):
        audit_log.record("export", note="json format")
        assert log_path.exists()
        data = json.loads(log_path.read_text())
        assert len(data) == 1
        assert data[0]["action"] == "export"

    def test_load_existing_log(self, log_path):
        existing = [
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "action": "diff",
                "source": ".env",
                "target": None,
                "keys_affected": [],
                "note": "",
            }
        ]
        log_path.write_text(json.dumps(existing))
        log = AuditLog(log_path)
        assert len(log.entries()) == 1
        assert log.entries()[0].action == "diff"

    def test_multiple_entries_appended(self, audit_log):
        audit_log.record("sync", source="a")
        audit_log.record("sync", source="b")
        assert len(audit_log.entries()) == 2

    def test_clear_removes_entries_and_file(self, audit_log, log_path):
        audit_log.record("diff")
        audit_log.clear()
        assert audit_log.entries() == []
        assert not log_path.exists()

    def test_keys_affected_stored(self, audit_log):
        audit_log.record("sync", keys_affected=["API_KEY", "DB_PASS"])
        entry = audit_log.entries()[0]
        assert "API_KEY" in entry.keys_affected

    def test_corrupted_log_falls_back_to_empty(self, log_path):
        log_path.write_text("not valid json")
        log = AuditLog(log_path)
        assert log.entries() == []
