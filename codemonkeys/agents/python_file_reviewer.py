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


def make_python_file_reviewer(
    files: list[str],
    *,
    model: str = "sonnet",
) -> AgentDefinition:
    """Reviews Python files for code quality and security issues."""
    file_list = "\n".join(f"- `{f}`" for f in files)

    has_test_files = any(_is_test_file(f) for f in files)
    has_prod_files = any(not _is_test_file(f) for f in files)

    checklists: list[str] = []
    if has_prod_files:
        checklists.extend([CODE_QUALITY, SECURITY_OBSERVATIONS, RESILIENCE_REVIEW])
    if has_test_files:
        checklists.append(TEST_QUALITY)

    checklist_block = "\n\n".join(checklists)

    return AgentDefinition(
        name=f"python_file_reviewer:{','.join(f.split('/')[-1] for f in files)}",
        model=model,
        system_prompt=f"""\
You review Python files for code quality and security issues.

## Files to Review

{file_list}

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
