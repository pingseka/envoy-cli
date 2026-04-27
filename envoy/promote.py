"""Promote env vars from one environment file to another."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class PromoteStatus(str, Enum):
    ADDED = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"


@dataclass
class PromoteEntry:
    key: str
    status: PromoteStatus
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == PromoteStatus.ADDED:
            return f"[added]   {self.key}"
        if self.status == PromoteStatus.UPDATED:
            return f"[updated] {self.key}"
        return f"[skipped] {self.key}"


@dataclass
class PromoteResult:
    entries: List[PromoteEntry] = field(default_factory=list)

    def added(self) -> List[PromoteEntry]:
        return [e for e in self.entries if e.status == PromoteStatus.ADDED]

    def updated(self) -> List[PromoteEntry]:
        return [e for e in self.entries if e.status == PromoteStatus.UPDATED]

    def skipped(self) -> List[PromoteEntry]:
        return [e for e in self.entries if e.status == PromoteStatus.SKIPPED]

    def summary(self) -> str:
        return (
            f"{len(self.added())} added, "
            f"{len(self.updated())} updated, "
            f"{len(self.skipped())} skipped"
        )


def promote_env(
    source_path: str,
    target_path: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Promote variables from source env to target env.

    Args:
        source_path: Path to the source .env file.
        target_path: Path to the target .env file.
        keys: Optional list of keys to promote; if None, promote all.
        overwrite: If True, overwrite existing keys in target.

    Returns:
        PromoteResult describing what was added, updated, or skipped.
    """
    source: Dict[str, str] = parse_env_file(source_path)
    target: Dict[str, str] = parse_env_file(target_path)

    result = PromoteResult()
    candidates = {k: v for k, v in source.items() if keys is None or k in keys}

    for key, value in candidates.items():
        if key in target:
            if overwrite:
                result.entries.append(
                    PromoteEntry(key, PromoteStatus.UPDATED, target[key], value)
                )
                target[key] = value
            else:
                result.entries.append(
                    PromoteEntry(key, PromoteStatus.SKIPPED, target[key], value)
                )
        else:
            result.entries.append(
                PromoteEntry(key, PromoteStatus.ADDED, None, value)
            )
            target[key] = value

    serialize_env(target, target_path)
    return result
