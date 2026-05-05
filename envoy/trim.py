"""Trim whitespace from env variable values."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class TrimStatus(str, Enum):
    TRIMMED = "trimmed"
    UNCHANGED = "unchanged"


@dataclass
class TrimEntry:
    key: str
    original: str
    trimmed: str
    status: TrimStatus

    def __str__(self) -> str:
        if self.status == TrimStatus.TRIMMED:
            return f"{self.key}: {self.original!r} -> {self.trimmed!r}"
        return f"{self.key}: unchanged"


@dataclass
class TrimResult:
    entries: List[TrimEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    def trimmed(self) -> List[TrimEntry]:
        return [e for e in self.entries if e.status == TrimStatus.TRIMMED]

    def unchanged(self) -> List[TrimEntry]:
        return [e for e in self.entries if e.status == TrimStatus.UNCHANGED]

    def summary(self) -> str:
        t = len(self.trimmed())
        u = len(self.unchanged())
        return f"{t} trimmed, {u} unchanged"


def trim_env(
    path: Path,
    keys: List[str] | None = None,
    write: bool = False,
) -> TrimResult:
    """Trim leading/trailing whitespace from env values.

    Args:
        path: Path to the .env file.
        keys: Optional list of keys to trim. If None, all keys are trimmed.
        write: If True, write the trimmed values back to the file.

    Returns:
        TrimResult with per-key entries and the resulting env dict.
    """
    env = parse_env_file(path)
    entries: List[TrimEntry] = []
    result_env: Dict[str, str] = {}

    for k, v in env.items():
        if keys is None or k in keys:
            trimmed_val = v.strip()
            status = TrimStatus.TRIMMED if trimmed_val != v else TrimStatus.UNCHANGED
            entries.append(TrimEntry(key=k, original=v, trimmed=trimmed_val, status=status))
            result_env[k] = trimmed_val
        else:
            entries.append(TrimEntry(key=k, original=v, trimmed=v, status=TrimStatus.UNCHANGED))
            result_env[k] = v

    result = TrimResult(entries=entries, env=result_env)

    if write:
        serialize_env(result_env, path)

    return result
