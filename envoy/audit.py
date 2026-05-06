"""Audit log for tracking .env file changes and sync operations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # e.g. 'sync', 'diff', 'export', 'profile_add'
    source: Optional[str]
    target: Optional[str]
    keys_affected: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            timestamp=data["timestamp"],
            action=data["action"],
            source=data.get("source"),
            target=data.get("target"),
            keys_affected=data.get("keys_affected", []),
            note=data.get("note", ""),
        )

    def __str__(self) -> str:
        parts = [f"[{self.timestamp}] {self.action.upper()}"]
        if self.source:
            parts.append(f"src={self.source}")
        if self.target:
            parts.append(f"tgt={self.target}")
        if self.keys_affected:
            parts.append(f"keys={','.join(self.keys_affected)}")
        if self.note:
            parts.append(f"({self.note})")
        return " | ".join(parts)


class AuditLog:
    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)
        self._entries: List[AuditEntry] = []
        if self.log_path.exists():
            self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self.log_path.read_text(encoding="utf-8"))
            self._entries = [AuditEntry.from_dict(e) for e in raw]
        except (json.JSONDecodeError, KeyError):
            self._entries = []

    def record(
        self,
        action: str,
        source: Optional[str] = None,
        target: Optional[str] = None,
        keys_affected: Optional[List[str]] = None,
        note: str = "",
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            source=source,
            target=target,
            keys_affected=keys_affected or [],
            note=note,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def _save(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2),
            encoding="utf-8",
        )

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def filter_by_action(self, action: str) -> List[AuditEntry]:
        """Return all entries matching the given action (case-insensitive)."""
        normalized = action.lower()
        return [e for e in self._entries if e.action.lower() == normalized]

    def last(self, n: int = 10) -> List[AuditEntry]:
        """Return the most recent *n* entries."""
        return list(self._entries[-n:])

    def clear(self) -> None:
        self._entries = []
        if self.log_path.exists():
            os.remove(self.log_path)
