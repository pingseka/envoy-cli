"""Key rotation: rename keys in bulk using a mapping of old->new names."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

from envoy.parser import parse_env_file, serialize_env


class RotateStatus(str, Enum):
    RENAMED = "renamed"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"  # new name already exists


@dataclass
class RotateEntry:
    old_key: str
    new_key: str
    status: RotateStatus

    def __str__(self) -> str:
        return f"{self.old_key} -> {self.new_key} [{self.status.value}]"


@dataclass
class RotateResult:
    entries: List[RotateEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    def renamed(self) -> List[RotateEntry]:
        return [e for e in self.entries if e.status == RotateStatus.RENAMED]

    def not_found(self) -> List[RotateEntry]:
        return [e for e in self.entries if e.status == RotateStatus.NOT_FOUND]

    def conflicts(self) -> List[RotateEntry]:
        return [e for e in self.entries if e.status == RotateStatus.CONFLICT]

    def ok(self) -> bool:
        return len(self.conflicts()) == 0 and len(self.not_found()) == 0

    def summary(self) -> str:
        parts = []
        if self.renamed():
            parts.append(f"{len(self.renamed())} renamed")
        if self.not_found():
            parts.append(f"{len(self.not_found())} not found")
        if self.conflicts():
            parts.append(f"{len(self.conflicts())} conflicts")
        return ", ".join(parts) if parts else "nothing to rotate"


def rotate_keys(env_path: Path, mapping: Dict[str, str]) -> RotateResult:
    """Apply a bulk rename mapping to an env file.

    Args:
        env_path: Path to the .env file.
        mapping: Dict of {old_key: new_key}.

    Returns:
        RotateResult with entries and the updated env dict.
    """
    env = parse_env_file(env_path)
    result = RotateResult(env=dict(env))

    for old_key, new_key in mapping.items():
        if old_key not in env:
            result.entries.append(RotateEntry(old_key, new_key, RotateStatus.NOT_FOUND))
            continue
        if new_key in env and new_key != old_key:
            result.entries.append(RotateEntry(old_key, new_key, RotateStatus.CONFLICT))
            continue
        value = result.env.pop(old_key)
        result.env[new_key] = value
        result.entries.append(RotateEntry(old_key, new_key, RotateStatus.RENAMED))

    return result


def apply_rotation(env_path: Path, result: RotateResult) -> None:
    """Write the rotated env back to disk."""
    serialize_env(result.env, env_path)
