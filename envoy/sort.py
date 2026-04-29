"""Sort keys in a .env file alphabetically or by custom order."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortResult:
    original_order: List[str]
    sorted_order: List[str]
    env: Dict[str, str]
    order: SortOrder

    @property
    def changed(self) -> bool:
        return self.original_order != self.sorted_order

    @property
    def moved_count(self) -> int:
        return sum(
            1 for i, k in enumerate(self.sorted_order)
            if i >= len(self.original_order) or self.original_order[i] != k
        )

    def summary(self) -> str:
        if not self.changed:
            return "Already sorted — no changes made."
        return (
            f"Sorted {len(self.sorted_order)} keys ({self.moved_count} moved) "
            f"in {self.order.value}ending order."
        )


def sort_env(
    path: Path,
    order: SortOrder = SortOrder.ASC,
    write: bool = False,
    group_prefixes: bool = False,
) -> SortResult:
    """Sort environment variables in *path* and optionally write back."""
    env = parse_env_file(path)
    original_order = list(env.keys())

    if group_prefixes:
        # Group keys by their prefix (before first '_'), sort within groups
        from collections import defaultdict
        groups: Dict[str, List[str]] = defaultdict(list)
        for key in original_order:
            prefix = key.split("_")[0] if "_" in key else key
            groups[prefix].append(key)
        sorted_keys: List[str] = []
        for prefix in sorted(groups.keys(), reverse=(order == SortOrder.DESC)):
            sorted_keys.extend(
                sorted(groups[prefix], reverse=(order == SortOrder.DESC))
            )
    else:
        sorted_keys = sorted(
            original_order, reverse=(order == SortOrder.DESC)
        )

    sorted_env = {k: env[k] for k in sorted_keys}

    if write:
        path.write_text(serialize_env(sorted_env))

    return SortResult(
        original_order=original_order,
        sorted_order=sorted_keys,
        env=sorted_env,
        order=order,
    )
