"""Split a .env file into multiple files by prefix or pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class SplitStatus(str, Enum):
    WRITTEN = "written"
    SKIPPED = "skipped"


@dataclass
class SplitEntry:
    output_file: str
    keys: List[str]
    status: SplitStatus

    def __str__(self) -> str:
        return f"{self.status.value}: {self.output_file} ({len(self.keys)} keys)"


@dataclass
class SplitResult:
    entries: List[SplitEntry] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)

    def written(self) -> List[SplitEntry]:
        return [e for e in self.entries if e.status == SplitStatus.WRITTEN]

    def skipped(self) -> List[SplitEntry]:
        return [e for e in self.entries if e.status == SplitStatus.SKIPPED]

    def summary(self) -> str:
        parts = [f"{len(self.written())} file(s) written"]
        if self.unmatched:
            parts.append(f"{len(self.unmatched)} key(s) unmatched")
        return ", ".join(parts)


def split_env_by_prefix(
    source: str,
    output_dir: str,
    prefixes: List[str],
    strip_prefix: bool = False,
    dry_run: bool = False,
) -> SplitResult:
    """Split env file into one file per prefix."""
    env = parse_env_file(source)
    out_path = Path(output_dir)
    result = SplitResult()
    matched_keys: set = set()

    for prefix in prefixes:
        subset = {
            (k[len(prefix):] if strip_prefix else k): v
            for k, v in env.items()
            if k.startswith(prefix)
        }
        original_keys = [k for k in env if k.startswith(prefix)]
        matched_keys.update(original_keys)
        filename = f"{prefix.lower().rstrip('_')}.env"
        out_file = str(out_path / filename)

        if not subset:
            result.entries.append(
                SplitEntry(output_file=out_file, keys=[], status=SplitStatus.SKIPPED)
            )
            continue

        if not dry_run:
            out_path.mkdir(parents=True, exist_ok=True)
            Path(out_file).write_text(serialize_env(subset))

        result.entries.append(
            SplitEntry(output_file=out_file, keys=original_keys, status=SplitStatus.WRITTEN)
        )

    result.unmatched = [k for k in env if k not in matched_keys]
    return result
