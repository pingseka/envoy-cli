"""Strip keys from a .env file by name or pattern."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, serialize_env


class StripStatus(str, Enum):
    REMOVED = "removed"
    SKIPPED = "skipped"


@dataclass
class StripEntry:
    key: str
    status: StripStatus

    def __str__(self) -> str:
        symbol = "-" if self.status == StripStatus.REMOVED else "~"
        return f"{symbol} {self.key} [{self.status.value}]"


@dataclass
class StripResult:
    entries: List[StripEntry] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)

    def removed(self) -> List[StripEntry]:
        return [e for e in self.entries if e.status == StripStatus.REMOVED]

    def skipped(self) -> List[StripEntry]:
        return [e for e in self.entries if e.status == StripStatus.SKIPPED]

    def summary(self) -> str:
        r = len(self.removed())
        s = len(self.skipped())
        return f"{r} key(s) removed, {s} key(s) not found"


def _matches_any(key: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(key, p) for p in patterns)


def strip_keys(
    env_path: str,
    patterns: List[str],
    *,
    dry_run: bool = False,
    output_path: Optional[str] = None,
) -> StripResult:
    """Remove keys matching *patterns* from *env_path*.

    Supports shell-style wildcards via fnmatch (e.g. ``AWS_*``).
    If *dry_run* is True the file is not modified.
    If *output_path* is given the result is written there instead of in-place.
    """
    env = parse_env_file(env_path)
    result = StripResult()

    kept: Dict[str, str] = {}
    for key, value in env.items():
        if _matches_any(key, patterns):
            result.entries.append(StripEntry(key=key, status=StripStatus.REMOVED))
        else:
            kept[key] = value

    # Report patterns that matched nothing
    matched_keys = {e.key for e in result.removed()}
    for pattern in patterns:
        if not any(fnmatch.fnmatch(k, pattern) for k in env):
            # Only add a skipped entry when it is a literal key name, not a
            # wildcard, so we don't flood output with unmatched globs.
            if "*" not in pattern and "?" not in pattern and "[" not in pattern:
                if pattern not in matched_keys:
                    result.entries.append(
                        StripEntry(key=pattern, status=StripStatus.SKIPPED)
                    )

    result.output = kept

    if not dry_run:
        dest = output_path or env_path
        serialize_env(kept, dest)

    return result
