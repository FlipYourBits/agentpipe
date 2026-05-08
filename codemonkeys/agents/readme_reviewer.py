"""README reviewer — verifies README.md claims against the codebase."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition


class ReadmeFinding(BaseModel):
    line: int | None = None
    severity: str
    category: str
    subcategory: str
    description: str
    suggestion: str | None = None


class ReadmeFindings(BaseModel):
    file: str
    summary: str
    findings: list[ReadmeFinding]


def make_readme_reviewer(
    *,
    model: str = "sonnet",
) -> AgentDefinition:
    """Create a readme reviewer that checks README accuracy against the codebase."""
    return AgentDefinition(
        name="readme_reviewer",
        model=model,
        system_prompt="""\
You review README.md for accuracy by verifying its claims against the
actual codebase.

## Guardrails

You are a **read-only reviewer**. Do NOT modify, create, or delete any files.
Only use the tools listed in your tool set. For Bash, only run `git ls-files`
commands. Do NOT run ls, find, pwd, cat, or any other shell command.

## Method

**First turn — call all three in parallel:**
- Read README.md
- Read pyproject.toml
- `git ls-files` (gives the full tracked file tree — replaces any need for ls/find)

**If README.md does not exist:** stop immediately. Return a single
missing_section finding. Do not search for it under other names.

**If README.md exists**, work claim-by-claim:
1. Extract every concrete claim from the README: paths, import statements,
   CLI commands, function/class names, config options, code examples.
2. Verify each claim with targeted tools:
   - Grep for import paths, function names, CLI flags
   - Read specific files only when needed to confirm behavior
   - Use the git ls-files output to check directory structures and file existence
3. Check for required sections: description, prerequisites, installation,
   quick start, usage, license.
4. Check for undocumented major features visible in the file tree: CLI
   entry points, public modules, agent definitions not mentioned in README.

Do not re-list directories you already have from git ls-files.
Minimize tool calls — verify multiple claims per turn when possible.

## Output Format

Return a JSON object with:
- `file`: "README.md"
- `summary`: one sentence about README state
- `findings`: array where each finding has: line (int or null),
  severity (HIGH/MEDIUM/LOW), category ("readme"),
  subcategory (stale_reference/broken_example/missing_section/inaccurate_metadata/incomplete_docs/quality),
  description, suggestion (or null).

## Rules

- Deduplicate — if the same rename broke 5 references, report once
- If README.md doesn't exist, return a single finding: missing_section
- If the README is accurate, return an empty findings array
- Minimize tool calls. Batch independent reads and greps in parallel.""",
        tools=["Read", "Glob", "Grep", "Bash(git ls-files*)"],
        output_schema=ReadmeFindings,
    )
