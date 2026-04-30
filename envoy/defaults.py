"""Apply default values to missing keys in an env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class DefaultStatus(str, Enum):
    APPLIED = "applied"
    SKIPPED = "skipped"  # key already present


@dataclass
class DefaultEntry:
    key: str
    value: str
    status: DefaultStatus

    def __str__(self) -> str:
        symbol = "+" if self.status == DefaultStatus.APPLIED else "="
        return f"[{symbol}] {self.key}={self.value}  ({self.status.value})"


@dataclass
class DefaultResult:
    entries: List[DefaultEntry] = field(default_factory=list)

    def applied(self) -> List[DefaultEntry]:
        return [e for e in self.entries if e.status == DefaultStatus.APPLIED]

    def skipped(self) -> List[DefaultEntry]:
        return [e for e in self.entries if e.status == DefaultStatus.SKIPPED]

    def summary(self) -> str:
        return (
            f"{len(self.applied())} default(s) applied, "
            f"{len(self.skipped())} already present"
        )


def apply_defaults(
    env: Dict[str, str],
    defaults: Dict[str, str],
) -> DefaultResult:
    """Return a new env dict with *defaults* filled in for missing keys.

    Keys that already exist in *env* are left unchanged.
    The result also carries a :class:`DefaultResult` describing what happened.
    """
    result = DefaultResult()
    for key, value in defaults.items():
        if key in env:
            result.entries.append(
                DefaultEntry(key=key, value=env[key], status=DefaultStatus.SKIPPED)
            )
        else:
            env[key] = value
            result.entries.append(
                DefaultEntry(key=key, value=value, status=DefaultStatus.APPLIED)
            )
    return result
