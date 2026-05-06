from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class TruncateStatus(str, Enum):
    TRUNCATED = "truncated"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"


@dataclass
class TruncateEntry:
    key: str
    original: str
    result: str
    status: TruncateStatus

    def __str__(self) -> str:
        if self.status == TruncateStatus.TRUNCATED:
            return f"{self.key}: truncated ({len(self.original)} -> {len(self.result)} chars)"
        return f"{self.key}: {self.status.value}"


@dataclass
class TruncateResult:
    entries: List[TruncateEntry] = field(default_factory=list)

    def truncated(self) -> List[TruncateEntry]:
        return [e for e in self.entries if e.status == TruncateStatus.TRUNCATED]

    def unchanged(self) -> List[TruncateEntry]:
        return [e for e in self.entries if e.status == TruncateStatus.UNCHANGED]

    def summary(self) -> str:
        t = len(self.truncated())
        u = len(self.unchanged())
        return f"{t} truncated, {u} unchanged"

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.result for e in self.entries}


def truncate_env(
    path: str,
    max_length: int,
    keys: List[str] | None = None,
    suffix: str = "...",
) -> TruncateResult:
    """Truncate values in an env file to at most *max_length* characters.

    If *keys* is provided only those keys are considered; others are marked
    SKIPPED.  The suffix (default ``"..."``) is appended when a value is cut
    and counts toward *max_length*.
    """
    if max_length < len(suffix):
        raise ValueError(
            f"max_length ({max_length}) must be >= suffix length ({len(suffix)})"
        )

    env = parse_env_file(path)
    result = TruncateResult()

    for key, value in env.items():
        if keys is not None and key not in keys:
            result.entries.append(
                TruncateEntry(key=key, original=value, result=value, status=TruncateStatus.SKIPPED)
            )
            continue

        if len(value) > max_length:
            cut = max_length - len(suffix)
            new_value = value[:cut] + suffix
            result.entries.append(
                TruncateEntry(key=key, original=value, result=new_value, status=TruncateStatus.TRUNCATED)
            )
        else:
            result.entries.append(
                TruncateEntry(key=key, original=value, result=value, status=TruncateStatus.UNCHANGED)
            )

    return result
