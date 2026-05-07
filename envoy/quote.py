"""Quote/unquote values in .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from envoy.parser import parse_env_file, serialize_env


class QuoteStyle(str, Enum):
    DOUBLE = "double"
    SINGLE = "single"
    NONE = "none"


class QuoteStatus(str, Enum):
    QUOTED = "quoted"
    UNQUOTED = "unquoted"
    SKIPPED = "skipped"


@dataclass
class QuoteEntry:
    key: str
    old_value: str
    new_value: str
    status: QuoteStatus

    def __str__(self) -> str:
        if self.status == QuoteStatus.SKIPPED:
            return f"{self.key}: skipped (already correct)"
        return f"{self.key}: {self.old_value!r} -> {self.new_value!r} ({self.status.value})"


@dataclass
class QuoteResult:
    entries: List[QuoteEntry] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    def changed(self) -> List[QuoteEntry]:
        return [e for e in self.entries if e.status != QuoteStatus.SKIPPED]

    def skipped(self) -> List[QuoteEntry]:
        return [e for e in self.entries if e.status == QuoteStatus.SKIPPED]

    def summary(self) -> str:
        c = len(self.changed())
        s = len(self.skipped())
        return f"{c} value(s) requoted, {s} skipped"


def _apply_quote(value: str, style: QuoteStyle) -> str:
    if style == QuoteStyle.DOUBLE:
        inner = value.replace('"', '\\"')
        return f'"{inner}"'
    if style == QuoteStyle.SINGLE:
        inner = value.replace("'", "\\'")
        return f"'{inner}'"
    # NONE — strip surrounding quotes
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def quote_env(
    source: str,
    style: QuoteStyle = QuoteStyle.DOUBLE,
    keys: List[str] | None = None,
) -> QuoteResult:
    """Re-quote values in *source* .env file path using *style*."""
    env = parse_env_file(source)
    result = QuoteResult(env=dict(env))

    for key, value in env.items():
        if keys is not None and key not in keys:
            result.entries.append(QuoteEntry(key, value, value, QuoteStatus.SKIPPED))
            continue

        new_value = _apply_quote(value, style)
        if new_value == value:
            result.entries.append(QuoteEntry(key, value, value, QuoteStatus.SKIPPED))
        else:
            status = QuoteStatus.UNQUOTED if style == QuoteStyle.NONE else QuoteStatus.QUOTED
            result.entries.append(QuoteEntry(key, value, new_value, status))
            result.env[key] = new_value

    return result
