"""Snapshot support: capture and restore .env file states."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


@dataclass
class Snapshot:
    label: str
    timestamp: str
    env_path: str
    data: Dict[str, str]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "env_path": self.env_path,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        return cls(
            label=d["label"],
            timestamp=d["timestamp"],
            env_path=d["env_path"],
            data=d["data"],
        )

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.label} ({self.env_path})"


@dataclass
class SnapshotStore:
    store_path: Path
    snapshots: List[Snapshot] = field(default_factory=list)

    def save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as fh:
            json.dump([s.to_dict() for s in self.snapshots], fh, indent=2)

    def load(self) -> None:
        if not self.store_path.exists():
            self.snapshots = []
            return
        with open(self.store_path, "r", encoding="utf-8") as fh:
            self.snapshots = [Snapshot.from_dict(d) for d in json.load(fh)]

    def add(self, snapshot: Snapshot) -> None:
        self.snapshots.append(snapshot)
        self.save()

    def get(self, label: str) -> Optional[Snapshot]:
        for s in reversed(self.snapshots):
            if s.label == label:
                return s
        return None

    def list_all(self) -> List[Snapshot]:
        return list(self.snapshots)

    def remove(self, label: str) -> bool:
        before = len(self.snapshots)
        self.snapshots = [s for s in self.snapshots if s.label != label]
        if len(self.snapshots) < before:
            self.save()
            return True
        return False


def capture_snapshot(env_path: str, label: str, store: SnapshotStore) -> Snapshot:
    data = parse_env_file(env_path)
    ts = datetime.now(timezone.utc).isoformat()
    snap = Snapshot(label=label, timestamp=ts, env_path=env_path, data=data)
    store.add(snap)
    return snap


def restore_snapshot(snapshot: Snapshot, target_path: Optional[str] = None) -> str:
    out_path = target_path or snapshot.env_path
    content = serialize_env(snapshot.data)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return out_path
