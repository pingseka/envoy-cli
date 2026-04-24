"""Tests for envoy.snapshot module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from envoy.snapshot import (
    Snapshot,
    SnapshotStore,
    capture_snapshot,
    restore_snapshot,
)


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(tmp_dir):
    p = tmp_dir / ".env"
    p.write_text("APP_NAME=envoy\nDEBUG=true\nSECRET_KEY=abc123\n")
    return str(p)


@pytest.fixture
def store(tmp_dir):
    s = SnapshotStore(store_path=tmp_dir / "snapshots.json")
    s.load()
    return s


class TestSnapshot:
    def test_to_dict_roundtrip(self):
        snap = Snapshot(
            label="v1",
            timestamp="2024-01-01T00:00:00+00:00",
            env_path=".env",
            data={"FOO": "bar"},
        )
        assert Snapshot.from_dict(snap.to_dict()) == snap

    def test_str_includes_label(self):
        snap = Snapshot(
            label="release",
            timestamp="2024-01-01T00:00:00+00:00",
            env_path=".env",
            data={},
        )
        assert "release" in str(snap)
        assert ".env" in str(snap)


class TestSnapshotStore:
    def test_empty_on_missing_file(self, store):
        assert store.list_all() == []

    def test_add_and_retrieve(self, store):
        snap = Snapshot("v1", "2024-01-01T00:00:00+00:00", ".env", {"K": "V"})
        store.add(snap)
        assert store.get("v1") is not None
        assert store.get("v1").data == {"K": "V"}

    def test_persists_to_disk(self, store):
        snap = Snapshot("v2", "2024-01-01T00:00:00+00:00", ".env", {"X": "1"})
        store.add(snap)
        store2 = SnapshotStore(store_path=store.store_path)
        store2.load()
        assert len(store2.list_all()) == 1
        assert store2.get("v2").data == {"X": "1"}

    def test_remove_existing(self, store):
        snap = Snapshot("v3", "2024-01-01T00:00:00+00:00", ".env", {})
        store.add(snap)
        removed = store.remove("v3")
        assert removed is True
        assert store.get("v3") is None

    def test_remove_nonexistent_returns_false(self, store):
        assert store.remove("ghost") is False

    def test_get_returns_latest_for_duplicate_labels(self, store):
        s1 = Snapshot("dup", "2024-01-01T00:00:00+00:00", ".env", {"V": "1"})
        s2 = Snapshot("dup", "2024-01-02T00:00:00+00:00", ".env", {"V": "2"})
        store.add(s1)
        store.add(s2)
        assert store.get("dup").data["V"] == "2"


class TestCaptureAndRestore:
    def test_capture_reads_env(self, env_file, store):
        snap = capture_snapshot(env_file, "initial", store)
        assert snap.data["APP_NAME"] == "envoy"
        assert snap.label == "initial"

    def test_restore_writes_file(self, env_file, store, tmp_dir):
        snap = capture_snapshot(env_file, "pre", store)
        target = str(tmp_dir / "restored.env")
        restore_snapshot(snap, target_path=target)
        assert Path(target).exists()
        content = Path(target).read_text()
        assert "APP_NAME" in content

    def test_restore_overwrites_original(self, env_file, store):
        snap = capture_snapshot(env_file, "backup", store)
        Path(env_file).write_text("APP_NAME=changed\n")
        restore_snapshot(snap)
        restored = Path(env_file).read_text()
        assert "envoy" in restored
