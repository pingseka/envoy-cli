"""Diff support for comparing .env files across environments."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, _is_secret_key


class DiffStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    is_secret: bool = False

    def display_value(self, value: Optional[str]) -> str:
        if value is None:
            return "<missing>"
        if self.is_secret:
            return "****"
        return value

    def __str__(self) -> str:
        if self.status == DiffStatus.ADDED:
            return f"+ {self.key}={self.display_value(self.new_value)}"
        elif self.status == DiffStatus.REMOVED:
            return f"- {self.key}={self.display_value(self.old_value)}"
        elif self.status == DiffStatus.CHANGED:
            return (
                f"~ {self.key}: {self.display_value(self.old_value)}"
                f" -> {self.display_value(self.new_value)}"
            )
        return f"  {self.key}={self.display_value(self.new_value)}"


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.status != DiffStatus.UNCHANGED for e in self.entries)

    @property
    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in DiffStatus}
        for entry in self.entries:
            counts[entry.status.value] += 1
        return counts

    def __str__(self) -> str:
        return "\n".join(str(e) for e in self.entries)


def diff_env_files(base_path: str, target_path: str, show_unchanged: bool = False) -> DiffResult:
    """Compare two .env files and return a DiffResult."""
    base = parse_env_file(base_path)
    target = parse_env_file(target_path)

    all_keys = sorted(set(base) | set(target))
    entries: List[DiffEntry] = []

    for key in all_keys:
        is_secret = _is_secret_key(key)
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            entries.append(DiffEntry(key, DiffStatus.REMOVED, old_value=base[key], is_secret=is_secret))
        elif not in_base and in_target:
            entries.append(DiffEntry(key, DiffStatus.ADDED, new_value=target[key], is_secret=is_secret))
        elif base[key] != target[key]:
            entries.append(DiffEntry(key, DiffStatus.CHANGED, old_value=base[key], new_value=target[key], is_secret=is_secret))
        elif show_unchanged:
            entries.append(DiffEntry(key, DiffStatus.UNCHANGED, new_value=target[key], is_secret=is_secret))

    return DiffResult(entries=entries)
