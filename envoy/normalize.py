"""Normalize .env file keys and values (case, whitespace, quoting)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from envoy.parser import parse_env_file, serialize_env


class NormalizeOp(str, Enum):
    KEY_UPPER = "key_upper"
    KEY_LOWER = "key_lower"
    VALUE_STRIP = "value_strip"
    VALUE_UNQUOTE = "value_unquote"


@dataclass
class NormalizeEntry:
    key: str
    original_key: str
    original_value: str
    normalized_key: str
    normalized_value: str
    ops_applied: List[NormalizeOp] = field(default_factory=list)

    def __str__(self) -> str:
        changes = ", ".join(op.value for op in self.ops_applied)
        return f"{self.original_key}={self.original_value!r} -> {self.normalized_key}={self.normalized_value!r} [{changes}]"


@dataclass
class NormalizeResult:
    entries: List[NormalizeEntry] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)

    def changed(self) -> List[NormalizeEntry]:
        return [
            e for e in self.entries
            if e.original_key != e.normalized_key or e.original_value != e.normalized_value
        ]

    def changed_count(self) -> int:
        return len(self.changed())

    def summary(self) -> str:
        total = len(self.entries)
        n = self.changed_count()
        return f"{n}/{total} key(s) normalized"


def normalize_env(
    path: str,
    key_case: str | None = None,
    strip_values: bool = False,
    unquote_values: bool = False,
) -> NormalizeResult:
    """Normalize keys/values in an env file according to specified operations."""
    env = parse_env_file(path)
    result = NormalizeResult()

    for orig_key, orig_value in env.items():
        ops: List[NormalizeOp] = []
        new_key = orig_key
        new_value = orig_value

        if key_case == "upper" and new_key != new_key.upper():
            new_key = new_key.upper()
            ops.append(NormalizeOp.KEY_UPPER)
        elif key_case == "lower" and new_key != new_key.lower():
            new_key = new_key.lower()
            ops.append(NormalizeOp.KEY_LOWER)

        if strip_values and new_value != new_value.strip():
            new_value = new_value.strip()
            ops.append(NormalizeOp.VALUE_STRIP)

        if unquote_values:
            unquoted = new_value
            if (
                (unquoted.startswith('"') and unquoted.endswith('"')) or
                (unquoted.startswith("'") and unquoted.endswith("'"))
            ) and len(unquoted) >= 2:
                unquoted = unquoted[1:-1]
            if unquoted != new_value:
                new_value = unquoted
                ops.append(NormalizeOp.VALUE_UNQUOTE)

        entry = NormalizeEntry(
            key=new_key,
            original_key=orig_key,
            original_value=orig_value,
            normalized_key=new_key,
            normalized_value=new_value,
            ops_applied=ops,
        )
        result.entries.append(entry)
        result.output[new_key] = new_value

    return result
