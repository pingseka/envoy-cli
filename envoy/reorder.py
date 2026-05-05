"""Reorder keys in a .env file according to a specified key list or alphabetically."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class ReorderStatus(str, Enum):
    MOVED = "moved"
    UNCHANGED = "unchanged"
    UNSPECIFIED = "unspecified"  # key exists in env but not in order list


@dataclass
class ReorderEntry:
    key: str
    old_index: int
    new_index: int
    status: ReorderStatus

    def __str__(self) -> str:
        if self.status == ReorderStatus.MOVED:
            return f"{self.key}: position {self.old_index} -> {self.new_index}"
        if self.status == ReorderStatus.UNSPECIFIED:
            return f"{self.key}: unspecified (appended at {self.new_index})"
        return f"{self.key}: unchanged at {self.new_index}"


@dataclass
class ReorderResult:
    entries: List[ReorderEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    def moved(self) -> List[ReorderEntry]:
        return [e for e in self.entries if e.status == ReorderStatus.MOVED]

    def unspecified(self) -> List[ReorderEntry]:
        return [e for e in self.entries if e.status == ReorderStatus.UNSPECIFIED]

    def summary(self) -> str:
        m = len(self.moved())
        u = len(self.unspecified())
        return f"{m} key(s) moved, {u} unspecified key(s) appended"


def reorder_env(
    source: Path,
    order: List[str],
    append_unspecified: bool = True,
) -> ReorderResult:
    """Reorder keys in *source* according to *order*.

    Keys not listed in *order* are appended at the end when
    *append_unspecified* is True, otherwise they are dropped.
    """
    env = parse_env_file(source)
    original_keys = list(env.keys())

    ordered: Dict[str, str] = {}
    for key in order:
        if key in env:
            ordered[key] = env[key]

    if append_unspecified:
        for key in original_keys:
            if key not in ordered:
                ordered[key] = env[key]

    entries: List[ReorderEntry] = []
    new_keys = list(ordered.keys())
    for new_idx, key in enumerate(new_keys):
        old_idx = original_keys.index(key) if key in original_keys else -1
        if key not in order:
            status = ReorderStatus.UNSPECIFIED
        elif old_idx == new_idx:
            status = ReorderStatus.UNCHANGED
        else:
            status = ReorderStatus.MOVED
        entries.append(ReorderEntry(key=key, old_index=old_idx, new_index=new_idx, status=status))

    return ReorderResult(entries=entries, env=ordered)
