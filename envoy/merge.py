"""Merge two .env files with conflict resolution strategies."""

from enum import Enum
from typing import Dict, Optional
from envoy.parser import parse_env_file, serialize_env


class MergeStrategy(str, Enum):
    OURS = "ours"       # prefer values from base file
    THEIRS = "theirs"   # prefer values from incoming file
    UNION = "union"     # keep all keys; base wins on conflict


class MergeConflict:
    def __init__(self, key: str, base_value: str, incoming_value: str) -> None:
        self.key = key
        self.base_value = base_value
        self.incoming_value = incoming_value

    def __repr__(self) -> str:  # pragma: no cover
        return f"MergeConflict(key={self.key!r})"


class MergeResult:
    def __init__(
        self,
        merged: Dict[str, str],
        conflicts: list,
        added: list,
        removed: list,
    ) -> None:
        self.merged = merged
        self.conflicts = conflicts
        self.added = added
        self.removed = removed

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.conflicts:
            parts.append(f"{len(self.conflicts)} conflict(s)")
        return ", ".join(parts) if parts else "no changes"


def merge_env_files(
    base_path: str,
    incoming_path: str,
    strategy: MergeStrategy = MergeStrategy.UNION,
) -> MergeResult:
    """Merge two env files and return a MergeResult."""
    base = parse_env_file(base_path)
    incoming = parse_env_file(incoming_path)

    merged: Dict[str, str] = {}
    conflicts = []
    added = []
    removed = []

    all_keys = set(base) | set(incoming)

    for key in sorted(all_keys):
        in_base = key in base
        in_incoming = key in incoming

        if in_base and not in_incoming:
            if strategy == MergeStrategy.THEIRS:
                removed.append(key)
            else:
                merged[key] = base[key]
        elif in_incoming and not in_base:
            merged[key] = incoming[key]
            added.append(key)
        else:
            # key exists in both
            if base[key] == incoming[key]:
                merged[key] = base[key]
            else:
                conflicts.append(MergeConflict(key, base[key], incoming[key]))
                if strategy == MergeStrategy.THEIRS:
                    merged[key] = incoming[key]
                else:  # OURS or UNION
                    merged[key] = base[key]

    return MergeResult(merged=merged, conflicts=conflicts, added=added, removed=removed)


def write_merged(result: MergeResult, output_path: str) -> None:
    """Write the merged env dict to a file."""
    serialize_env(result.merged, output_path)
