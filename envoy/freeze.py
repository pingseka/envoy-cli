"""Freeze: lock env file values to prevent accidental changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class FreezeStatus(str, Enum):
    LOCKED = "locked"
    ALREADY_LOCKED = "already_locked"
    SKIPPED = "skipped"


@dataclass
class FreezeEntry:
    key: str
    status: FreezeStatus

    def __str__(self) -> str:
        return f"{self.key}: {self.status.value}"


@dataclass
class FreezeResult:
    entries: List[FreezeEntry] = field(default_factory=list)
    lockfile: Optional[Path] = None

    def locked(self) -> List[FreezeEntry]:
        return [e for e in self.entries if e.status == FreezeStatus.LOCKED]

    def already_locked(self) -> List[FreezeEntry]:
        return [e for e in self.entries if e.status == FreezeStatus.ALREADY_LOCKED]

    def skipped(self) -> List[FreezeEntry]:
        return [e for e in self.entries if e.status == FreezeStatus.SKIPPED]

    def summary(self) -> str:
        return (
            f"{len(self.locked())} locked, "
            f"{len(self.already_locked())} already locked, "
            f"{len(self.skipped())} skipped"
        )


def freeze_env(
    env_path: Path,
    keys: Optional[List[str]] = None,
    lockfile_path: Optional[Path] = None,
) -> FreezeResult:
    """Lock specified keys (or all keys) by recording them in a lockfile."""
    env = parse_env_file(env_path)
    if lockfile_path is None:
        lockfile_path = env_path.with_suffix(".lock")

    existing_locks: Dict[str, str] = {}
    if lockfile_path.exists():
        existing_locks = parse_env_file(lockfile_path)

    target_keys = keys if keys is not None else list(env.keys())
    entries: List[FreezeEntry] = []
    new_locks = dict(existing_locks)

    for key in target_keys:
        if key not in env:
            entries.append(FreezeEntry(key=key, status=FreezeStatus.SKIPPED))
            continue
        if key in existing_locks:
            entries.append(FreezeEntry(key=key, status=FreezeStatus.ALREADY_LOCKED))
        else:
            new_locks[key] = env[key]
            entries.append(FreezeEntry(key=key, status=FreezeStatus.LOCKED))

    lockfile_path.write_text(serialize_env(new_locks))
    return FreezeResult(entries=entries, lockfile=lockfile_path)


def check_frozen(
    env_path: Path,
    lockfile_path: Optional[Path] = None,
) -> Dict[str, bool]:
    """Return mapping of locked key -> whether current value matches locked value."""
    env = parse_env_file(env_path)
    if lockfile_path is None:
        lockfile_path = env_path.with_suffix(".lock")
    if not lockfile_path.exists():
        return {}
    locks = parse_env_file(lockfile_path)
    return {key: env.get(key) == val for key, val in locks.items()}
