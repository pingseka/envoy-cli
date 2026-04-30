"""Key/value transformation utilities for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class TransformStatus(Enum):
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"


@dataclass
class TransformEntry:
    key: str
    old_value: str
    new_value: str
    status: TransformStatus

    def __str__(self) -> str:
        if self.status == TransformStatus.CHANGED:
            return f"{self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"{self.key}: {self.status.value}"


@dataclass
class TransformResult:
    entries: List[TransformEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    def changed(self) -> List[TransformEntry]:
        return [e for e in self.entries if e.status == TransformStatus.CHANGED]

    def unchanged(self) -> List[TransformEntry]:
        return [e for e in self.entries if e.status == TransformStatus.UNCHANGED]

    def summary(self) -> str:
        c = len(self.changed())
        t = len(self.entries)
        return f"{c}/{t} keys transformed"


def transform_env(
    path: str,
    fn: Callable[[str, str], Optional[str]],
    keys: Optional[List[str]] = None,
) -> TransformResult:
    """Apply *fn(key, value) -> new_value | None* to each key in the env file.

    If *fn* returns ``None`` the key is skipped (left unchanged).
    If *keys* is provided only those keys are considered.
    """
    env = parse_env_file(path)
    result = TransformResult(env=dict(env))

    for key, value in env.items():
        if keys is not None and key not in keys:
            result.entries.append(
                TransformEntry(key, value, value, TransformStatus.SKIPPED)
            )
            continue

        new_value = fn(key, value)
        if new_value is None or new_value == value:
            result.entries.append(
                TransformEntry(key, value, value, TransformStatus.UNCHANGED)
            )
        else:
            result.env[key] = new_value
            result.entries.append(
                TransformEntry(key, value, new_value, TransformStatus.CHANGED)
            )

    return result
