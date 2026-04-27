"""Flatten nested/duplicate env keys by applying a prefix filter or deduplication strategy."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from envoy.parser import parse_env_file


class FlattenStatus(str, Enum):
    KEPT = "kept"
    DUPLICATE = "duplicate"
    RENAMED = "renamed"


@dataclass
class FlattenEntry:
    key: str
    value: str
    status: FlattenStatus
    original_key: str = ""

    def __str__(self) -> str:
        if self.status == FlattenStatus.RENAMED:
            return f"[renamed] {self.original_key} -> {self.key}"
        if self.status == FlattenStatus.DUPLICATE:
            return f"[duplicate] {self.key}"
        return f"[kept] {self.key}"


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)

    def kept(self) -> List[FlattenEntry]:
        return [e for e in self.entries if e.status == FlattenStatus.KEPT]

    def duplicates(self) -> List[FlattenEntry]:
        return [e for e in self.entries if e.status == FlattenStatus.DUPLICATE]

    def renamed(self) -> List[FlattenEntry]:
        return [e for e in self.entries if e.status == FlattenStatus.RENAMED]

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries if e.status != FlattenStatus.DUPLICATE}

    def summary(self) -> str:
        return (
            f"{len(self.kept())} kept, "
            f"{len(self.duplicates())} duplicates removed, "
            f"{len(self.renamed())} renamed"
        )


def flatten_env(
    path: str,
    strip_prefix: str = "",
    keep_first: bool = True,
) -> FlattenResult:
    """Parse *path* and flatten it: strip an optional prefix from keys and
    deduplicate repeated keys (keeping first or last occurrence)."""
    env = parse_env_file(path)
    result = FlattenResult()
    seen: Dict[str, str] = {}

    for raw_key, value in env.items():
        final_key = raw_key
        status = FlattenStatus.KEPT
        original_key = ""

        if strip_prefix and raw_key.startswith(strip_prefix):
            final_key = raw_key[len(strip_prefix):]
            status = FlattenStatus.RENAMED
            original_key = raw_key

        if final_key in seen:
            if keep_first:
                result.entries.append(
                    FlattenEntry(key=final_key, value=value,
                                 status=FlattenStatus.DUPLICATE,
                                 original_key=original_key or final_key)
                )
                continue
            else:
                # overwrite — mark previous as duplicate
                for e in result.entries:
                    if e.key == final_key and e.status != FlattenStatus.DUPLICATE:
                        e.status = FlattenStatus.DUPLICATE
                        break

        seen[final_key] = value
        result.entries.append(
            FlattenEntry(key=final_key, value=value,
                         status=status, original_key=original_key)
        )

    return result
