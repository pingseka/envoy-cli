"""Prune unused or duplicate keys from a .env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Sequence

from envoy.parser import parse_env_file, serialize_env


class PruneStatus(str, Enum):
    REMOVED_DUPLICATE = "removed_duplicate"
    REMOVED_EMPTY = "removed_empty"
    KEPT = "kept"


@dataclass
class PruneEntry:
    key: str
    status: PruneStatus
    value: str = ""

    def __str__(self) -> str:
        if self.status == PruneStatus.KEPT:
            return f"  {self.key} (kept)"
        return f"  {self.key} [{self.status.value}]"


@dataclass
class PruneResult:
    entries: List[PruneEntry] = field(default_factory=list)

    def removed(self) -> List[PruneEntry]:
        return [
            e for e in self.entries
            if e.status != PruneStatus.KEPT
        ]

    def kept(self) -> List[PruneEntry]:
        return [e for e in self.entries if e.status == PruneStatus.KEPT]

    def summary(self) -> str:
        r = len(self.removed())
        return f"Pruned {r} key(s)."


def prune_env(
    path: Path,
    *,
    remove_empty: bool = True,
    dry_run: bool = False,
) -> PruneResult:
    """Remove duplicate and optionally empty keys from *path*.

    The first occurrence of a duplicate key is kept; subsequent ones are
    removed.  When *dry_run* is True the file is not modified.
    """
    env = parse_env_file(path)
    result = PruneResult()
    seen: Dict[str, bool] = {}
    final: Dict[str, str] = {}

    for key, value in env.items():
        if key in seen:
            result.entries.append(
                PruneEntry(key=key, status=PruneStatus.REMOVED_DUPLICATE, value=value)
            )
            continue
        if remove_empty and value == "":
            result.entries.append(
                PruneEntry(key=key, status=PruneStatus.REMOVED_EMPTY, value=value)
            )
            seen[key] = True
            continue
        seen[key] = True
        final[key] = value
        result.entries.append(
            PruneEntry(key=key, status=PruneStatus.KEPT, value=value)
        )

    if not dry_run:
        path.write_text(serialize_env(final))

    return result
