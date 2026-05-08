"""Fixer agent — applies fixes from any list of items."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition


class FixResult(BaseModel):
    """What the fixer did."""

    applied: list[str]
    skipped: list[str]
    summary: str


def _default_formatter(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, BaseModel):
        d = item.model_dump(exclude_none=True)
        return " | ".join(f"{k}: {v}" for k, v in d.items())
    if isinstance(item, dict):
        return " | ".join(f"{k}: {v}" for k, v in item.items() if v is not None)
    return str(item)


def make_fixer(
    items: list[Any],
    *,
    formatter: Callable[[Any], str] | None = None,
    model: str = "opus",
) -> AgentDefinition:
    fmt = formatter or _default_formatter
    numbered = "\n".join(f"{i}. {fmt(item)}" for i, item in enumerate(items, 1))

    return AgentDefinition(
        name="fixer",
        model=model,
        system_prompt=f"""\
You are a code fixer. Apply the fixes described below to the codebase.

## Findings to Fix

{numbered}

## Automated Checks

Linting (ruff) runs automatically after every file edit — you will see
the results as additional context. Type checking (pyright) and linting
run automatically when you finish — if they fail, you will be asked to
fix the issues before completing. You do not need to run these tools yourself.

## Process

For each finding:
1. Read the relevant file to understand the full context around the issue
2. Apply the fix — use the suggestion as guidance but use your judgment for the best implementation
3. If lint errors appear after an edit, fix them before moving on

## Rules

- Only modify what's needed to fix each finding. Do not refactor surrounding code.
- If a finding's suggestion is unclear or would break something, skip it and explain why.
- Report which findings you applied and which you skipped.""",
        tools=["Read", "Edit", "Grep"],
        hooks={
            "PostToolUse": [
                ("Edit", "uv run ruff check --fix {file_path} && uv run ruff format {file_path}"),
            ],
            "Stop": [
                (None, "uv run ruff check ."),
                (None, "uv run pyright ."),
            ],
        },
        output_schema=FixResult,
    )
