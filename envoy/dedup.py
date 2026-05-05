"""Detect and remove duplicate values across keys in an env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from envoy.parser import parse_env_file, serialize_env


class DedupStatus(str, Enum):
    KEPT = "kept"
    REMOVED = "removed"


@dataclass
class DedupEntry:
    key: str
    value: str
    status: DedupStatus
    duplicate_of: str | None = None

    def __str__(self) -> str:
        if self.status == DedupStatus.REMOVED:
            return f"[removed] {self.key} (duplicate of '{self.duplicate_of}')"
        return f"[kept]    {self.key}={self.value}"


@dataclass
class DedupResult:
    entries: List[DedupEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def removed(self) -> List[DedupEntry]:
        return [e for e in self.entries if e.status == DedupStatus.REMOVED]

    @property
    def kept(self) -> List[DedupEntry]:
        return [e for e in self.entries if e.status == DedupStatus.KEPT]

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    def summary(self) -> str:
        return (
            f"{len(self.kept)} keys kept, {self.removed_count} duplicate(s) removed"
        )


def dedup_env(
    env_path: str,
    keep: str = "first",
) -> DedupResult:
    """Find keys that share the same value and remove duplicates.

    Args:
        env_path: Path to the .env file.
        keep: Which occurrence to keep — 'first' (default) or 'last'.

    Returns:
        DedupResult with entries and the deduplicated env dict.
    """
    env = parse_env_file(env_path)
    # Build value -> list of keys mapping (in insertion order)
    value_keys: Dict[str, List[str]] = {}
    for k, v in env.items():
        value_keys.setdefault(v, []).append(k)

    # Decide which key to keep for each duplicated value group
    survivor: Dict[str, str] = {}  # key -> value for survivors
    removed_map: Dict[str, str] = {}  # key -> kept_key

    for v, keys in value_keys.items():
        if len(keys) == 1:
            survivor[keys[0]] = v
        else:
            chosen = keys[0] if keep == "first" else keys[-1]
            survivor[chosen] = v
            for k in keys:
                if k != chosen:
                    removed_map[k] = chosen

    entries: List[DedupEntry] = []
    result_env: Dict[str, str] = {}
    for k, v in env.items():
        if k in removed_map:
            entries.append(
                DedupEntry(
                    key=k,
                    value=v,
                    status=DedupStatus.REMOVED,
                    duplicate_of=removed_map[k],
                )
            )
        else:
            entries.append(DedupEntry(key=k, value=v, status=DedupStatus.KEPT))
            result_env[k] = v

    return DedupResult(entries=entries, env=result_env)
