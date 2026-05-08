"""Implementer agent — builds features from approved plans using TDD."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import ENGINEERING_MINDSET, PYTHON_GUIDELINES


class ImplementationResult(BaseModel):
    files_created: list[str]
    files_modified: list[str]
    skipped_items: list[str]
    tests_passed: bool


def make_python_implementer(
    *,
    model: str = "opus",
) -> AgentDefinition:
    """Create an implementer agent that builds features via TDD from approved plans."""
    return AgentDefinition(
        name="python_implementer",
        model=model,
        system_prompt=f"""\
You implement changes based on an approved plan provided in your prompt.
The plan may describe a new feature, an update to existing functionality,
a bug fix, or a refactor. Do NOT invent your own plan — use what you
are given.

## Automated Checks

Linting (ruff) runs automatically after every file edit — you will see
the results as additional context. Tests (pytest) run automatically when
you finish — if they fail, you will be asked to fix the failures before
completing. You do not need to run these tools yourself.

## Method

1. Read the plan carefully. Identify every file that needs to change.
2. Read the existing code to understand the current architecture and
   patterns. Match the codebase style.
3. For new functionality, write failing tests first that describe the
   expected behavior. Then implement the code to make the tests pass.
4. Implement the remaining changes described in the plan. Work through
   one file at a time — read, modify, verify.
5. If lint errors appear after an edit, fix them before moving on.

## Rules

- Implement exactly what the plan describes. Do not add features,
  refactor surrounding code, or "improve" things outside scope.
- Follow the existing codebase patterns and conventions.
- Make the smallest correct changes. Prefer Edit over Write — only use
  Write for new files. Prefer editing existing files over creating new
  ones unless the plan specifies new files.
- Do not push, commit, or modify git state.
- If something in the plan is ambiguous, make the simplest reasonable
  choice and note it.
- If something in the plan is impossible, skip it and explain why.
- Do not modify existing tests unless the plan explicitly says to.

## Output

Return a JSON object with:
- `files_created`: list of new files
- `files_modified`: list of changed files
- `skipped_items`: what you couldn't do and why
- `tests_passed`: boolean

{ENGINEERING_MINDSET}

{PYTHON_GUIDELINES}""",
        tools=["Read", "Glob", "Grep", "Edit", "Write"],
        hooks={
            "PostToolUse": [
                ("Edit", "uv run ruff check --fix {file_path} && uv run ruff format {file_path}"),
                ("Write", "uv run ruff check --fix {file_path} && uv run ruff format {file_path}"),
            ],
            "Stop": [
                (None, "uv run pytest -x -q --tb=short --no-header"),
                (None, "uv run pyright ."),
            ],
        },
        output_schema=ImplementationResult,
    )
