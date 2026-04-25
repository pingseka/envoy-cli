"""Lint .env files for common issues and style violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class LintSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    line: int
    key: Optional[str]
    message: str
    severity: LintSeverity

    def __str__(self) -> str:
        loc = f"line {self.line}" + (f" ({self.key})" if self.key else "")
        return f"[{self.severity.value.upper()}] {loc}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == LintSeverity.ERROR for i in self.issues)

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]


def lint_env_file(path: str) -> LintResult:
    """Run all lint checks against an .env file."""
    result = LintResult()
    seen_keys: Dict[str, int] = {}

    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # Blank lines are fine; skip
        if not line.strip():
            continue

        # Skip comment lines
        if line.lstrip().startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(
                line=lineno, key=None,
                message="Line is not a valid KEY=VALUE pair",
                severity=LintSeverity.ERROR,
            ))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.issues.append(LintIssue(
                line=lineno, key=None,
                message="Empty key",
                severity=LintSeverity.ERROR,
            ))
            continue

        if key != key.upper():
            result.issues.append(LintIssue(
                line=lineno, key=key,
                message="Key should be UPPER_SNAKE_CASE",
                severity=LintSeverity.WARNING,
            ))

        if " " in key:
            result.issues.append(LintIssue(
                line=lineno, key=key,
                message="Key contains spaces",
                severity=LintSeverity.ERROR,
            ))

        if key in seen_keys:
            result.issues.append(LintIssue(
                line=lineno, key=key,
                message=f"Duplicate key (first seen on line {seen_keys[key]})",
                severity=LintSeverity.ERROR,
            ))
        else:
            seen_keys[key] = lineno

        if value == "":
            result.issues.append(LintIssue(
                line=lineno, key=key,
                message="Value is empty",
                severity=LintSeverity.WARNING,
            ))

    return result
