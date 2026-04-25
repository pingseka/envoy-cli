"""File watcher for .env files — detects changes and triggers callbacks."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class WatchEvent:
    path: str
    previous_hash: Optional[str]
    current_hash: str
    changed_keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        keys = ", ".join(self.changed_keys) if self.changed_keys else "(unknown)"
        return f"WatchEvent({self.path!r}, changed={keys})"


def _file_hash(path: str) -> Optional[str]:
    """Return SHA-256 hex digest of file contents, or None if unreadable."""
    try:
        data = Path(path).read_bytes()
        return hashlib.sha256(data).hexdigest()
    except OSError:
        return None


def _changed_keys(old_path: str, new_path: str) -> List[str]:
    """Return list of keys that differ between two env file states."""
    from envoy.parser import parse_env_file

    try:
        old = parse_env_file(old_path)
    except Exception:
        old = {}
    try:
        new = parse_env_file(new_path)
    except Exception:
        new = {}

    all_keys = set(old) | set(new)
    return sorted(k for k in all_keys if old.get(k) != new.get(k))


class EnvWatcher:
    """Poll one or more .env files for changes."""

    def __init__(self, paths: List[str], interval: float = 1.0) -> None:
        self.paths = paths
        self.interval = interval
        self._hashes: Dict[str, Optional[str]] = {p: _file_hash(p) for p in paths}
        self._callbacks: List[Callable[[WatchEvent], None]] = []

    def on_change(self, callback: Callable[[WatchEvent], None]) -> None:
        self._callbacks.append(callback)

    def poll(self) -> List[WatchEvent]:
        """Check all watched paths once; return list of WatchEvents for changed files."""
        events: List[WatchEvent] = []
        for path in self.paths:
            current = _file_hash(path)
            previous = self._hashes.get(path)
            if current != previous:
                keys = _changed_keys(path, path) if previous is None else _changed_keys(path, path)
                event = WatchEvent(
                    path=path,
                    previous_hash=previous,
                    current_hash=current or "",
                    changed_keys=keys,
                )
                self._hashes[path] = current
                events.append(event)
                for cb in self._callbacks:
                    cb(event)
        return events

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll until interrupted or max_iterations reached."""
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                self.poll()
                time.sleep(self.interval)
                iteration += 1
        except KeyboardInterrupt:
            pass
