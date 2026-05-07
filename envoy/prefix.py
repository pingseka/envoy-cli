"""Add or remove a prefix from environment variable keys."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class PrefixStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    SKIPPED = "skipped"


@dataclass
class PrefixEntry:
    original_key: str
    new_key: str
    value: str
    status: PrefixStatus

    def __str__(self) -> str:
        return f"{self.original_key} -> {self.new_key} [{self.status.value}]"


@dataclass
class PrefixResult:
    entries: List[PrefixEntry]
    output_path: str

    def changed(self) -> List[PrefixEntry]:
        return [e for e in self.entries if e.status != PrefixStatus.SKIPPED]

    def skipped(self) -> List[PrefixEntry]:
        return [e for e in self.entries if e.status == PrefixStatus.SKIPPED]

    def summary(self) -> str:
        c = len(self.changed())
        s = len(self.skipped())
        return f"{c} key(s) renamed, {s} skipped"


def add_prefix(env_path: str, prefix: str, output_path: str | None = None) -> PrefixResult:
    """Add a prefix to all keys in the env file."""
    env = parse_env_file(env_path)
    entries: List[PrefixEntry] = []
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        if key.startswith(prefix):
            new_key = key
            status = PrefixStatus.SKIPPED
        else:
            new_key = f"{prefix}{key}"
            status = PrefixStatus.ADDED
        new_env[new_key] = value
        entries.append(PrefixEntry(original_key=key, new_key=new_key, value=value, status=status))

    dest = output_path or env_path
    serialize_env(new_env, dest)
    return PrefixResult(entries=entries, output_path=dest)


def remove_prefix(env_path: str, prefix: str, output_path: str | None = None) -> PrefixResult:
    """Remove a prefix from all matching keys in the env file."""
    env = parse_env_file(env_path)
    entries: List[PrefixEntry] = []
    new_env: Dict[str, str] = {}

    for key, value in env.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            status = PrefixStatus.REMOVED
        else:
            new_key = key
            status = PrefixStatus.SKIPPED
        new_env[new_key] = value
        entries.append(PrefixEntry(original_key=key, new_key=new_key, value=value, status=status))

    dest = output_path or env_path
    serialize_env(new_env, dest)
    return PrefixResult(entries=entries, output_path=dest)
