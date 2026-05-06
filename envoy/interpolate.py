"""Variable interpolation for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import re

_VAR_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class InterpolateStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNCHANGED = "unchanged"


@dataclass
class InterpolateEntry:
    key: str
    original: str
    result: str
    status: InterpolateStatus
    missing: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.status == InterpolateStatus.RESOLVED:
            return f"{self.key}: '{self.original}' -> '{self.result}'"
        if self.status == InterpolateStatus.UNRESOLVED:
            return f"{self.key}: unresolved refs {self.missing}"
        return f"{self.key}: unchanged"


@dataclass
class InterpolateResult:
    entries: List[InterpolateEntry] = field(default_factory=list)

    def resolved(self) -> List[InterpolateEntry]:
        return [e for e in self.entries if e.status == InterpolateStatus.RESOLVED]

    def unresolved(self) -> List[InterpolateEntry]:
        return [e for e in self.entries if e.status == InterpolateStatus.UNRESOLVED]

    def to_dict(self) -> Dict[str, str]:
        return {e.key: e.result for e in self.entries}

    def summary(self) -> str:
        r = len(self.resolved())
        u = len(self.unresolved())
        return f"{r} resolved, {u} unresolved"


def _interpolate_value(
    value: str, env: Dict[str, str]
) -> tuple[str, List[str]]:
    missing: List[str] = []

    def replacer(m: re.Match) -> str:
        var = m.group(1) or m.group(2)
        if var in env:
            return env[var]
        missing.append(var)
        return m.group(0)

    result = _VAR_RE.sub(replacer, value)
    return result, missing


def interpolate_env(
    env: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
) -> InterpolateResult:
    """Interpolate variable references in env values.

    References like $VAR or ${VAR} are replaced using *context* (defaults to
    the env itself for self-referential resolution).
    """
    lookup = dict(env)
    if context:
        lookup.update(context)

    result = InterpolateResult()
    for key, value in env.items():
        if not _VAR_RE.search(value):
            result.entries.append(
                InterpolateEntry(key, value, value, InterpolateStatus.UNCHANGED)
            )
            continue
        resolved, missing = _interpolate_value(value, lookup)
        status = (
            InterpolateStatus.UNRESOLVED if missing else InterpolateStatus.RESOLVED
        )
        result.entries.append(
            InterpolateEntry(key, value, resolved, status, missing)
        )
    return result
