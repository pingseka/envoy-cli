"""Pin specific env var keys to required values or types for enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file


class PinViolationKind(str, Enum):
    MISSING = "missing"
    VALUE_MISMATCH = "value_mismatch"
    PATTERN_MISMATCH = "pattern_mismatch"


@dataclass
class PinViolation:
    key: str
    kind: PinViolationKind
    expected: Optional[str] = None
    actual: Optional[str] = None

    def __str__(self) -> str:
        if self.kind == PinViolationKind.MISSING:
            return f"[{self.kind}] '{self.key}' is required but not present"
        if self.kind == PinViolationKind.VALUE_MISMATCH:
            return f"[{self.kind}] '{self.key}': expected '{self.expected}', got '{self.actual}'"
        return f"[{self.kind}] '{self.key}': value does not match pattern '{self.expected}'"


@dataclass
class PinResult:
    violations: List[PinViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "All pinned keys satisfied."
        lines = [str(v) for v in self.violations]
        return "\n".join(lines)


def check_pins(
    env_path: str,
    pins: Dict[str, Optional[str]],
) -> PinResult:
    """Check that keys in *pins* exist in the env file.

    If a pin value is not None the actual value must match exactly.
    If a pin value starts with 're:' the remainder is treated as a regex.
    """
    import re

    env = parse_env_file(env_path)
    violations: List[PinViolation] = []

    for key, expected in pins.items():
        if key not in env:
            violations.append(PinViolation(key=key, kind=PinViolationKind.MISSING))
            continue

        actual = env[key]

        if expected is None:
            continue

        if expected.startswith("re:"):
            pattern = expected[3:]
            if not re.fullmatch(pattern, actual):
                violations.append(
                    PinViolation(
                        key=key,
                        kind=PinViolationKind.PATTERN_MISMATCH,
                        expected=pattern,
                        actual=actual,
                    )
                )
        elif actual != expected:
            violations.append(
                PinViolation(
                    key=key,
                    kind=PinViolationKind.VALUE_MISMATCH,
                    expected=expected,
                    actual=actual,
                )
            )

    return PinResult(violations=violations)
