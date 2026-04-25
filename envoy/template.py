"""Template rendering for .env files with variable substitution."""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass, field

_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class RenderIssue:
    key: str
    variable: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] ${{{self.variable}}}: {self.message}"


@dataclass
class RenderResult:
    rendered: Dict[str, str] = field(default_factory=dict)
    issues: List[RenderIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0


def _find_variables(value: str) -> List[str]:
    """Return all variable names referenced in a value string."""
    matches = _VAR_PATTERN.findall(value)
    return [m[0] or m[1] for m in matches]


def _substitute(value: str, context: Dict[str, str]) -> str:
    """Replace ${VAR} and $VAR references with values from context."""
    def replacer(match: re.Match) -> str:
        name = match.group(1) or match.group(2)
        return context.get(name, match.group(0))

    return _VAR_PATTERN.sub(replacer, value)


def render_env(
    env: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> RenderResult:
    """Render an env dict by substituting variable references.

    Args:
        env: The environment variables to render.
        context: Extra variables available for substitution (defaults to env itself).
        strict: If True, unresolved variables are recorded as issues.

    Returns:
        RenderResult with rendered values and any issues found.
    """
    ctx: Dict[str, str] = dict(env)
    if context:
        ctx.update(context)

    result = RenderResult()

    for key, raw_value in env.items():
        refs = _find_variables(raw_value)
        rendered_value = _substitute(raw_value, ctx)

        for ref in refs:
            if ref not in ctx:
                issue = RenderIssue(
                    key=key,
                    variable=ref,
                    message="undefined variable",
                )
                result.issues.append(issue)

        result.rendered[key] = rendered_value

    return result
