"""Track and display change history for .env files."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HistoryEntry:
    timestamp: str
    action: str          # e.g. 'set', 'delete', 'import'
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    author: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "author": self.author,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            timestamp=data["timestamp"],
            action=data["action"],
            key=data["key"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            author=data.get("author", ""),
            note=data.get("note", ""),
        )

    def __str__(self) -> str:
        parts = [f"[{self.timestamp}] {self.action.upper()} {self.key}"]
        if self.author:
            parts.append(f"by {self.author}")
        if self.note:
            parts.append(f"({self.note})")
        return " ".join(parts)


@dataclass
class HistoryLog:
    path: Path
    entries: List[HistoryEntry] = field(default_factory=list)

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [HistoryEntry.from_dict(e) for e in raw.get("entries", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [e.to_dict() for e in self.entries]}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record(self, action: str, key: str, old_value: Optional[str] = None,
               new_value: Optional[str] = None, author: str = "", note: str = "") -> HistoryEntry:
        entry = HistoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            key=key,
            old_value=old_value,
            new_value=new_value,
            author=author,
            note=note,
        )
        self.entries.append(entry)
        return entry

    def for_key(self, key: str) -> List[HistoryEntry]:
        return [e for e in self.entries if e.key == key]

    def recent(self, n: int = 20) -> List[HistoryEntry]:
        return self.entries[-n:]
