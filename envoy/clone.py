"""Clone an env file, optionally filtering or renaming keys during copy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class CloneStatus(str, Enum):
    COPIED = "copied"
    SKIPPED = "skipped"
    RENAMED = "renamed"


@dataclass
class CloneEntry:
    source_key: str
    dest_key: str
    value: str
    status: CloneStatus

    def __str__(self) -> str:
        if self.source_key != self.dest_key:
            return f"{self.source_key} -> {self.dest_key} [{self.status.value}]"
        return f"{self.source_key} [{self.status.value}]"


@dataclass
class CloneResult:
    entries: List[CloneEntry] = field(default_factory=list)
    destination: str = ""

    def copied(self) -> List[CloneEntry]:
        return [e for e in self.entries if e.status == CloneStatus.COPIED]

    def renamed(self) -> List[CloneEntry]:
        return [e for e in self.entries if e.status == CloneStatus.RENAMED]

    def skipped(self) -> List[CloneEntry]:
        return [e for e in self.entries if e.status == CloneStatus.SKIPPED]

    def summary(self) -> str:
        return (
            f"{len(self.copied())} copied, "
            f"{len(self.renamed())} renamed, "
            f"{len(self.skipped())} skipped -> {self.destination}"
        )


def clone_env(
    source: str,
    destination: str,
    prefix_filter: Optional[str] = None,
    key_map: Optional[Dict[str, str]] = None,
    strip_prefix: bool = False,
) -> CloneResult:
    """Clone env from source to destination with optional filtering and renaming."""
    env = parse_env_file(source)
    key_map = key_map or {}
    result = CloneResult(destination=destination)
    output: Dict[str, str] = {}

    for key, value in env.items():
        if prefix_filter and not key.startswith(prefix_filter):
            result.entries.append(CloneEntry(key, key, value, CloneStatus.SKIPPED))
            continue

        dest_key = key
        if strip_prefix and prefix_filter and key.startswith(prefix_filter):
            dest_key = key[len(prefix_filter):]
        if key in key_map:
            dest_key = key_map[key]

        status = CloneStatus.RENAMED if dest_key != key else CloneStatus.COPIED
        result.entries.append(CloneEntry(key, dest_key, value, status))
        output[dest_key] = value

    Path(destination).write_text(serialize_env(output))
    return result
