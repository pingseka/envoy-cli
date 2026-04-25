"""Tests for envoy.watch."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from envoy.watch import EnvWatcher, WatchEvent, _file_hash


@pytest.fixture
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and gives back its path."""
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


class TestFileHash:
    def test_returns_string_for_existing_file(self, tmp_env):
        path = tmp_env("a.env", "KEY=val\n")
        h = _file_hash(path)
        assert isinstance(h, str) and len(h) == 64

    def test_returns_none_for_missing_file(self, tmp_path):
        h = _file_hash(str(tmp_path / "ghost.env"))
        assert h is None

    def test_changes_when_content_changes(self, tmp_env):
        path = tmp_env("b.env", "KEY=1\n")
        h1 = _file_hash(path)
        Path(path).write_text("KEY=2\n")
        h2 = _file_hash(path)
        assert h1 != h2


class TestWatchEvent:
    def test_str_includes_path(self):
        ev = WatchEvent(path=".env", previous_hash="aaa", current_hash="bbb", changed_keys=["FOO"])
        assert ".env" in str(ev)
        assert "FOO" in str(ev)

    def test_str_no_keys_shows_unknown(self):
        ev = WatchEvent(path=".env", previous_hash=None, current_hash="bbb")
        assert "unknown" in str(ev)


class TestEnvWatcher:
    def test_no_events_when_unchanged(self, tmp_env):
        path = tmp_env("c.env", "A=1\n")
        watcher = EnvWatcher([path])
        events = watcher.poll()
        assert events == []

    def test_detects_change_after_write(self, tmp_env):
        path = tmp_env("d.env", "A=1\n")
        watcher = EnvWatcher([path])
        # mutate file
        Path(path).write_text("A=2\n")
        events = watcher.poll()
        assert len(events) == 1
        assert events[0].path == path

    def test_callback_is_called_on_change(self, tmp_env):
        path = tmp_env("e.env", "X=hello\n")
        watcher = EnvWatcher([path])
        received = []
        watcher.on_change(received.append)
        Path(path).write_text("X=world\n")
        watcher.poll()
        assert len(received) == 1
        assert received[0].path == path

    def test_no_duplicate_events_on_second_poll(self, tmp_env):
        path = tmp_env("f.env", "Y=1\n")
        watcher = EnvWatcher([path])
        Path(path).write_text("Y=2\n")
        watcher.poll()  # first poll picks it up
        events2 = watcher.poll()  # second poll — no change
        assert events2 == []

    def test_multiple_files_tracked(self, tmp_env):
        p1 = tmp_env("g1.env", "A=1\n")
        p2 = tmp_env("g2.env", "B=2\n")
        watcher = EnvWatcher([p1, p2])
        Path(p2).write_text("B=99\n")
        events = watcher.poll()
        assert len(events) == 1
        assert events[0].path == p2

    def test_watch_respects_max_iterations(self, tmp_env):
        path = tmp_env("h.env", "Z=0\n")
        watcher = EnvWatcher([path], interval=0.01)
        # Should return without hanging
        watcher.watch(max_iterations=2)
