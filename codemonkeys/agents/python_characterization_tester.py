"""Characterization test writer — locks current behavior for uncovered files."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import PYTHON_GUIDELINES


class CharacterizationResult(BaseModel):
    files_tested: list[str]
    test_files_created: list[str]
    test_files_modified: list[str]
    skipped: list[str]
    all_passed: bool


def make_python_characterization_tester(
    files: list[str],
    import_context: str,
    uncovered_lines: dict[str, list[int]] | None = None,
    *,
    model: str = "sonnet",
) -> AgentDefinition:
    file_list = "\n".join(f"- `{f}`" for f in files)

    uncovered_section = ""
    if uncovered_lines:
        for f, lines in uncovered_lines.items():
            if lines:
                line_str = ", ".join(str(ln) for ln in lines[:50])
                uncovered_section += f"\n### `{f}` — uncovered lines: {line_str}\n"

    return AgentDefinition(
        name=f"python_characterization_tester:{len(files)}_files",
        model=model,
        system_prompt=f"""\
You write characterization tests that lock the current behavior of existing code.
Your goal is to maximize line coverage for the files listed below.

## Automated Checks

Coverage data (pytest --cov) is collected automatically when you start — use
it to identify uncovered lines. Tests (pytest) run automatically when you
finish — if they fail, you will be asked to fix the failures before completing.
You do not need to run pytest or coverage yourself.

## Files to Test

{file_list}

## Import Context

{import_context}

## Uncovered Lines
{uncovered_section}

## Method

1. Review the coverage data provided at session start to identify uncovered lines.
2. Read each source file to understand what it does.
3. Check if a test file already exists (e.g. `tests/test_<stem>.py`). If it does,
   add new tests to it rather than overwriting. If not, create a new test file.
4. Write tests that exercise the uncovered lines.
5. Focus on testing observable behavior: return values, side effects, exceptions.
6. If a test fails, fix the TEST — never modify the source code.

## Rules

- Tests MUST pass. They characterize what the code does now, not what it should do.
- Do not modify source files under any circumstances.
- Do not modify `conftest.py` files.
- Do not add type stubs or fixtures unless necessary for import.
- Prefer simple, direct tests over elaborate fixtures.
- Prefer Edit over Write when adding tests to an existing file.
- Use `unittest.mock.patch` sparingly — only when the code has side effects
  (file I/O, network, subprocess) that cannot be avoided.
- Name tests descriptively: `test_<function>_<scenario>`.

## Output

Return a JSON object with:
- `files_tested`: source files that got tests
- `test_files_created`: new test files
- `test_files_modified`: existing test files that were updated
- `skipped`: files skipped and why
- `all_passed`: boolean

{PYTHON_GUIDELINES}""",
        tools=[
            "Read",
            "Edit(tests/*)",
            "Write(tests/*)",
            "Glob",
            "Grep",
        ],
        hooks={
            "SubagentStart": [
                (None, "uv run pytest --cov=. --cov-report=term-missing -q --no-header"),
            ],
            "Stop": [
                (None, "uv run pytest -x -q --tb=short --no-header"),
            ],
        },
        output_schema=CharacterizationResult,
    )
