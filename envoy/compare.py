"""Compare two .env files and produce a structured report."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, _is_secret_key


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class CompareEntry:
    key: str
    change: ChangeType
    base_value: Optional[str] = None
    target_value: Optional[str] = None
    is_secret: bool = False

    def display_base(self) -> str:
        if self.base_value is None:
            return ""
        return "***" if self.is_secret else self.base_value

    def display_target(self) -> str:
        if self.target_value is None:
            return ""
        return "***" if self.is_secret else self.target_value

    def __str__(self) -> str:
        symbol = {ChangeType.ADDED: "+", ChangeType.REMOVED: "-",
                  ChangeType.MODIFIED: "~", ChangeType.UNCHANGED: " "}[self.change]
        return f"{symbol} {self.key}: {self.display_base()!r} -> {self.display_target()!r}"


@dataclass
class CompareResult:
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def added(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.change == ChangeType.ADDED]

    @property
    def removed(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.change == ChangeType.REMOVED]

    @property
    def modified(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.change == ChangeType.MODIFIED]

    @property
    def unchanged(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.change == ChangeType.UNCHANGED]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def summary(self) -> str:
        return (f"+{len(self.added)} added, -{len(self.removed)} removed, "
                f"~{len(self.modified)} modified, {len(self.unchanged)} unchanged")


def compare_env_files(base_path: str, target_path: str,
                      include_unchanged: bool = False) -> CompareResult:
    """Compare two .env files and return a CompareResult."""
    base: Dict[str, str] = parse_env_file(base_path)
    target: Dict[str, str] = parse_env_file(target_path)
    all_keys = sorted(set(base) | set(target))
    entries: List[CompareEntry] = []

    for key in all_keys:
        secret = _is_secret_key(key)
        if key not in base:
            entries.append(CompareEntry(key, ChangeType.ADDED,
                                        target_value=target[key], is_secret=secret))
        elif key not in target:
            entries.append(CompareEntry(key, ChangeType.REMOVED,
                                        base_value=base[key], is_secret=secret))
        elif base[key] != target[key]:
            entries.append(CompareEntry(key, ChangeType.MODIFIED,
                                        base_value=base[key], target_value=target[key],
                                        is_secret=secret))
        elif include_unchanged:
            entries.append(CompareEntry(key, ChangeType.UNCHANGED,
                                        base_value=base[key], target_value=target[key],
                                        is_secret=secret))

    return CompareResult(entries=entries)
