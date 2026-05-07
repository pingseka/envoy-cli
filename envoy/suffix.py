"""Add or remove a suffix from environment variable keys."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class SuffixStatus(str, Enum):
    CHANGED = "changed"
    SKIPPED = "skipped"
    REMOVED = "removed"


@dataclass
class SuffixEntry:
    old_key: str
    new_key: str
    value: str
    status: SuffixStatus

    def __str__(self) -> str:
        if self.status == SuffixStatus.CHANGED:
            return f"{self.old_key} -> {self.new_key}"
        if self.status == SuffixStatus.REMOVED:
            return f"{self.old_key} (suffix removed -> {self.new_key})"
        return f"{self.old_key} (skipped)"


@dataclass
class SuffixResult:
    entries: List[SuffixEntry]
    env: Dict[str, str]

    def changed(self) -> List[SuffixEntry]:
        return [e for e in self.entries if e.status == SuffixStatus.CHANGED]

    def skipped(self) -> List[SuffixEntry]:
        return [e for e in self.entries if e.status == SuffixStatus.SKIPPED]

    def removed(self) -> List[SuffixEntry]:
        return [e for e in self.entries if e.status == SuffixStatus.REMOVED]

    def summary(self) -> str:
        return (
            f"{len(self.changed())} changed, "
            f"{len(self.skipped())} skipped, "
            f"{len(self.removed())} removed"
        )


def add_suffix(path: str, suffix: str, keys: List[str] | None = None) -> SuffixResult:
    """Append *suffix* to matching keys (all keys if *keys* is None)."""
    env = parse_env_file(path)
    entries: List[SuffixEntry] = []
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        if keys is None or key in keys:
            new_key = f"{key}{suffix}"
            entries.append(SuffixEntry(key, new_key, value, SuffixStatus.CHANGED))
            new_env[new_key] = value
        else:
            entries.append(SuffixEntry(key, key, value, SuffixStatus.SKIPPED))
            new_env[key] = value

    return SuffixResult(entries=entries, env=new_env)


def remove_suffix(path: str, suffix: str, keys: List[str] | None = None) -> SuffixResult:
    """Strip *suffix* from matching keys that end with it."""
    env = parse_env_file(path)
    entries: List[SuffixEntry] = []
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        target = keys is None or key in keys
        if target and key.endswith(suffix):
            new_key = key[: -len(suffix)]
            entries.append(SuffixEntry(key, new_key, value, SuffixStatus.REMOVED))
            new_env[new_key] = value
        else:
            entries.append(SuffixEntry(key, key, value, SuffixStatus.SKIPPED))
            new_env[key] = value

    return SuffixResult(entries=entries, env=new_env)


def write_suffix_result(result: SuffixResult, path: str) -> None:
    """Persist the transformed env to *path*."""
    serialize_env(result.env, path)
