"""Scope filtering: restrict env keys to a named subset defined by prefix or pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeResult:
    scope_name: str
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.matched) + len(self.excluded)

    def summary(self) -> str:
        return (
            f"Scope '{self.scope_name}': {len(self.matched)} matched, "
            f"{len(self.excluded)} excluded (total {self.total})"
        )


def filter_by_prefix(
    env: Dict[str, str],
    prefix: str,
    scope_name: Optional[str] = None,
    strip_prefix: bool = False,
) -> ScopeResult:
    """Return keys whose names start with *prefix*.

    If *strip_prefix* is True the prefix is removed from matched keys.
    """
    name = scope_name or prefix
    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}
    for key, value in env.items():
        if key.startswith(prefix):
            out_key = key[len(prefix):] if strip_prefix else key
            matched[out_key] = value
        else:
            excluded[key] = value
    return ScopeResult(scope_name=name, matched=matched, excluded=excluded)


def filter_by_pattern(
    env: Dict[str, str],
    pattern: str,
    scope_name: Optional[str] = None,
) -> ScopeResult:
    """Return keys whose names match the given regex *pattern*."""
    name = scope_name or pattern
    compiled = re.compile(pattern)
    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}
    for key, value in env.items():
        if compiled.search(key):
            matched[key] = value
        else:
            excluded[key] = value
    return ScopeResult(scope_name=name, matched=matched, excluded=excluded)


def filter_by_keys(
    env: Dict[str, str],
    keys: List[str],
    scope_name: Optional[str] = None,
) -> ScopeResult:
    """Return only the explicitly listed *keys*."""
    name = scope_name or "explicit"
    key_set = set(keys)
    matched = {k: v for k, v in env.items() if k in key_set}
    excluded = {k: v for k, v in env.items() if k not in key_set}
    return ScopeResult(scope_name=name, matched=matched, excluded=excluded)
