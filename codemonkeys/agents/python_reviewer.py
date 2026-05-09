"""Per-file Python reviewer agent."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import (
    CODE_QUALITY,
    PYTHON_GUIDELINES,
    RESILIENCE_REVIEW,
    SECURITY_OBSERVATIONS,
    TEST_QUALITY,
)


class Finding(BaseModel):
    file: str
    line: int | None = None
    severity: str
    category: str
    title: str
    description: str
    suggestion: str | None = None


class FileFindings(BaseModel):
    results: list[Finding]


def _is_test_file(path: str) -> bool:
    return "/tests/" in path or path.startswith("tests/") or path.endswith("_test.py")


def make_python_reviewer(
    file: str,
    *,
    model: str = "sonnet",
) -> AgentDefinition:
    """Reviews a single Python file for code quality and security issues."""
    is_test = _is_test_file(file)

    checklists: list[str] = []
    if not is_test:
        checklists.extend([CODE_QUALITY, SECURITY_OBSERVATIONS, RESILIENCE_REVIEW])
    if is_test:
        checklists.append(TEST_QUALITY)

    checklist_block = "\n\n".join(checklists)

    return AgentDefinition(
        name=f"python_reviewer:{file.split('/')[-1]}",
        model=model,
        system_prompt=f"""\
You review Python files for code quality and security issues.

## File to Review

`{file}`

{PYTHON_GUIDELINES}

{checklist_block}

## Output Format

Return a JSON object with a "results" array containing one Finding per issue found.
Each Finding has: file, line (int or null), severity (high/medium/low/info),
category (one of: CODE_QUALITY, SECURITY, RESILIENCE, TEST_QUALITY),
title, description, suggestion (or null).

Only report findings at 80%+ confidence with concrete scenarios.

## Guardrails

You are a read-only reviewer. Do NOT modify any files.""",
        tools=["Read", "Grep"],
        output_schema=FileFindings,
    )
