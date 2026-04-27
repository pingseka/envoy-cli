"""Group env keys by prefix or pattern into named sections."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class GroupResult:
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    def total(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    def summary(self) -> str:
        parts = [f"{name}({len(keys)})" for name, keys in self.groups.items()]
        if self.ungrouped:
            parts.append(f"ungrouped({len(self.ungrouped)})")
        return ", ".join(parts) if parts else "no keys"


def group_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    strip_prefix: bool = False,
) -> GroupResult:
    """Partition env keys into groups based on matching prefixes."""
    result = GroupResult()
    assigned: set = set()

    for prefix in prefixes:
        group: Dict[str, str] = {}
        for key, value in env.items():
            if key.startswith(prefix):
                out_key = key[len(prefix):] if strip_prefix else key
                group[out_key] = value
                assigned.add(key)
        result.groups[prefix] = group

    for key, value in env.items():
        if key not in assigned:
            result.ungrouped[key] = value

    return result


def group_by_pattern(
    env: Dict[str, str],
    patterns: Dict[str, str],
) -> GroupResult:
    """Partition env keys into named groups based on regex patterns.

    Args:
        env: The environment dict to group.
        patterns: Mapping of group_name -> regex pattern string.
    """
    result = GroupResult()
    assigned: set = set()
    compiled = {name: re.compile(pat) for name, pat in patterns.items()}

    for name, regex in compiled.items():
        group: Dict[str, str] = {}
        for key, value in env.items():
            if regex.search(key):
                group[key] = value
                assigned.add(key)
        result.groups[name] = group

    for key, value in env.items():
        if key not in assigned:
            result.ungrouped[key] = value

    return result
