"""Cross-file architecture and design reviewer agent."""

from __future__ import annotations

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import DESIGN_REVIEW, HARDENING_CHECKLIST


class ArchitectureFinding(BaseModel):
    files: list[str]
    severity: str
    category: str
    subcategory: str
    title: str
    description: str
    suggestion: str | None = None


class ArchitectureFindings(BaseModel):
    files_reviewed: list[str]
    findings: list[ArchitectureFinding]


def make_architecture_reviewer(
    *,
    files: list[str],
    file_summaries: list[dict[str, str]],
    structural_metadata: str = "",
    model: str = "opus",
) -> AgentDefinition:
    """Create an architecture reviewer scoped to the given files.

    AST structural metadata is collected automatically via a SubagentStart
    hook. If ``structural_metadata`` is also passed, it is included in the
    system prompt as a pre-computed supplement.
    """
    summaries_text = "\n".join(
        f"- `{s['file']}`: {s['summary']}" for s in file_summaries
    )

    metadata_section = ""
    if structural_metadata:
        metadata_section = f"""
## Pre-computed Structural Metadata

{structural_metadata}
"""

    files_arg = " ".join(files)

    return AgentDefinition(
        name=f"architecture_reviewer:{len(files)}_files",
        model=model,
        system_prompt=f"""\
You review a codebase for cross-file design issues. You have been given:

1. **Structural metadata** — imports, function signatures, class hierarchies,
   and decorators extracted via static analysis (ast). This is deterministic
   and complete. It is injected automatically at session start.
2. **Per-file summaries** — one-sentence descriptions from per-file reviewers
   who already read the source code.

Use these to identify cross-file design problems. Prefer the metadata and
summaries over reading full files — they are your primary source. Only read a
file when you need to verify a specific detail that the metadata doesn't cover.

## Guardrails

You are a **read-only reviewer**. Do NOT modify, create, or delete any files.
Do NOT run commands, install packages, or modify git state. Your only job is
to analyze and report findings.
{metadata_section}
## Per-File Summaries

{summaries_text}

## Method

1. Analyze the import graph for dependency direction, coupling, and cycles.
2. Compare function signatures and class interfaces across files for consistency.
3. Check whether files doing similar work use the same paradigm (async/sync,
   classes/functions, similar patterns).
4. Cross-reference summaries to find duplicated responsibilities or communication
   mismatches.
5. Report only genuine cross-file issues — per-file quality and security problems
   were already caught by per-file reviewers.

## Output Format

Return a JSON object with:
- `files_reviewed`: list of file paths reviewed
- `findings`: array of findings, each with: files, severity (HIGH/MEDIUM/LOW),
  category ("design"), subcategory (matching a checklist heading below),
  title, description, suggestion (or null).

## Rules

- Only report findings at 80%+ confidence
- `files` must list ALL files involved in the finding
- `subcategory` must match a checklist heading below
- If the codebase has no cross-file design issues, return an empty findings array
- Do NOT report per-file quality or security issues
- Do NOT report formatting or type errors

{DESIGN_REVIEW}

{HARDENING_CHECKLIST}""",
        tools=["Read"],
        hooks={
            "SubagentStart": [
                (None, f"uv run python -m codemonkeys.core.analysis {files_arg}"),
            ],
        },
        output_schema=ArchitectureFindings,
    )
