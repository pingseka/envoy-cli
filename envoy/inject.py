"""Inject key-value pairs into an existing .env file without overwriting existing keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class InjectStatus(Enum):
    ADDED = "added"
    SKIPPED = "skipped"  # key already exists and overwrite=False
    UPDATED = "updated"  # key existed and overwrite=True


@dataclass
class InjectEntry:
    key: str
    value: str
    status: InjectStatus

    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.key}={self.value}"


@dataclass
class InjectResult:
    entries: List[InjectEntry] = field(default_factory=list)

    def added(self) -> List[InjectEntry]:
        return [e for e in self.entries if e.status == InjectStatus.ADDED]

    def updated(self) -> List[InjectEntry]:
        return [e for e in self.entries if e.status == InjectStatus.UPDATED]

    def skipped(self) -> List[InjectEntry]:
        return [e for e in self.entries if e.status == InjectStatus.SKIPPED]

    def summary(self) -> str:
        return (
            f"{len(self.added())} added, "
            f"{len(self.updated())} updated, "
            f"{len(self.skipped())} skipped"
        )


def inject_env(
    target: Path,
    pairs: Dict[str, str],
    overwrite: bool = False,
) -> InjectResult:
    """Inject *pairs* into *target* .env file.

    Args:
        target: Path to the .env file to modify.
        pairs: Mapping of key -> value to inject.
        overwrite: When True, existing keys are updated; otherwise they are skipped.

    Returns:
        An :class:`InjectResult` describing what happened to each key.
    """
    existing: Dict[str, str] = parse_env_file(target) if target.exists() else {}
    result = InjectResult()

    for key, value in pairs.items():
        if key in existing:
            if overwrite:
                existing[key] = value
                result.entries.append(InjectEntry(key, value, InjectStatus.UPDATED))
            else:
                result.entries.append(InjectEntry(key, existing[key], InjectStatus.SKIPPED))
        else:
            existing[key] = value
            result.entries.append(InjectEntry(key, value, InjectStatus.ADDED))

    target.write_text(serialize_env(existing))
    return result
