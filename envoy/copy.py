"""Copy keys between .env files with optional overwrite control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class CopyStatus(str, Enum):
    COPIED = "copied"
    SKIPPED = "skipped"  # key already exists in target and overwrite=False
    NOT_FOUND = "not_found"  # key not present in source


@dataclass
class CopyEntry:
    key: str
    status: CopyStatus
    value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == CopyStatus.COPIED:
            return f"[copied]  {self.key}"
        if self.status == CopyStatus.SKIPPED:
            return f"[skipped] {self.key} (already exists)"
        return f"[missing] {self.key} (not found in source)"


@dataclass
class CopyResult:
    entries: List[CopyEntry] = field(default_factory=list)

    @property
    def copied(self) -> List[CopyEntry]:
        return [e for e in self.entries if e.status == CopyStatus.COPIED]

    @property
    def skipped(self) -> List[CopyEntry]:
        return [e for e in self.entries if e.status == CopyStatus.SKIPPED]

    @property
    def not_found(self) -> List[CopyEntry]:
        return [e for e in self.entries if e.status == CopyStatus.NOT_FOUND]

    def summary(self) -> str:
        return (
            f"{len(self.copied)} copied, "
            f"{len(self.skipped)} skipped, "
            f"{len(self.not_found)} not found"
        )


def copy_keys(
    source_path: str,
    target_path: str,
    keys: List[str],
    overwrite: bool = False,
) -> CopyResult:
    """Copy specific keys from source env file into target env file."""
    source: Dict[str, str] = parse_env_file(source_path)
    target: Dict[str, str] = parse_env_file(target_path)

    result = CopyResult()

    for key in keys:
        if key not in source:
            result.entries.append(CopyEntry(key=key, status=CopyStatus.NOT_FOUND))
            continue

        if key in target and not overwrite:
            result.entries.append(CopyEntry(key=key, status=CopyStatus.SKIPPED))
            continue

        target[key] = source[key]
        result.entries.append(
            CopyEntry(key=key, status=CopyStatus.COPIED, value=source[key])
        )

    serialize_env(target, target_path)
    return result
