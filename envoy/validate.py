"""Validation module for .env file entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ValidationSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: ValidationSeverity

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == ValidationSeverity.WARNING for i in self.issues)

    @property
    def is_valid(self) -> bool:
        return not self.has_errors

    def errors(self) -> List[ValidationIssue]:
        """Return only ERROR-severity issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def warnings(self) -> List[ValidationIssue]:
        """Return only WARNING-severity issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def __len__(self) -> int:
        return len(self.issues)


_KEY_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_EMPTY_VALUE_KEYS_WARN = True


def validate_env(
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
    disallow_empty_values: bool = False,
) -> ValidationResult:
    """Validate a parsed env dictionary.

    Args:
        env: Mapping of key -> value from parse_env_file.
        required_keys: Keys that must be present.
        disallow_empty_values: Treat empty values as errors.

    Returns:
        A ValidationResult with any found issues.
    """
    result = ValidationResult()

    for key in env:
        if not _KEY_PATTERN.match(key):
            result.issues.append(
                ValidationIssue(
                    key=key,
                    message=(
                        f"Key '{key}' does not follow UPPER_SNAKE_CASE convention."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )

        value = env[key]
        if disallow_empty_values and value == "":
            result.issues.append(
                ValidationIssue(
                    key=key,
                    message="Value is empty.",
                    severity=ValidationSeverity.ERROR,
                )
            )
        elif value == "":
            result.issues.append(
                ValidationIssue(
                    key=key,
                    message="Value is empty.",
                    severity=ValidationSeverity.WARNING,
                )
            )

    for req in required_keys or []:
        if req not in env:
            result.issues.append(
                ValidationIssue(
                    key=req,
                    message=f"Required key '{req}' is missing.",
                    severity=ValidationSeverity.ERROR,
                )
            )

    return result
