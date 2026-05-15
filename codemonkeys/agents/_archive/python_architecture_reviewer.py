"""Cross-file Python architecture and design reviewer agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from codemonkeys.core.analysis import analyze_files, format_analysis
from codemonkeys.core.discovery import discover_files
from codemonkeys.core.types import AgentDefinition, Severity
from codemonkeys.prompts import DESIGN_REVIEW


class ArchitectureFinding(BaseModel):
    """A single cross-file design issue; ``files`` lists every file involved."""

    files: list[str]
    severity: Severity
    category: Literal["design"]
    subcategory: str
    title: str
    description: str
    suggestion: str | None = None


class ArchitectureFindings(BaseModel):
    files_reviewed: list[str]
    findings: list[ArchitectureFinding]


def format_findings_markdown(result: ArchitectureFindings) -> str:
    """Convert architecture findings to a numbered markdown list."""
    lines = ["# Architecture Review Findings", ""]
    if not result.findings:
        lines.append("No cross-file design issues found.")
        return "\n".join(lines)

    for i, f in enumerate(result.findings, 1):
        files = ", ".join(f"`{p}`" for p in f.files)
        lines.append(f"## {i}. [{f.severity.upper()}] {f.title}")
        lines.append("")
        lines.append(f"**Category:** {f.subcategory}  ")
        lines.append(f"**Files:** {files}")
        lines.append("")
        lines.append(f.description)
        if f.suggestion:
            lines.append("")
            lines.append(f"**Suggestion:** {f.suggestion}")
        lines.append("")

    return "\n".join(lines)


_ROLE = (
    "You review a codebase for cross-file design issues. You have been given "
    "structural metadata (imports, function signatures, class hierarchies) "
    "extracted via static analysis. Use the Read tool to inspect files when "
    "the metadata doesn't cover what you need."
)

_RULES = (
    "## Rules\n\n"
    "- You are a read-only reviewer. Do not modify, create, or delete any files.\n"
    "- Do not run commands, install packages, or modify git state.\n"
    "- Only report findings at 80%+ confidence.\n"
    "- `files` must list all files involved in the finding.\n"
    "- `subcategory` must match a checklist heading.\n"
    "- If the codebase has no cross-file design issues, return an empty findings array.\n"
    "- Do not report per-file quality, security, formatting, or type issues."
)

_METHOD = (
    "## Method\n\n"
    "1. Analyze the import graph for dependency direction, coupling, and cycles.\n"
    "2. Compare function signatures and class interfaces across files for consistency.\n"
    "3. Check whether files doing similar work use the same paradigm "
    "(async/sync, classes/functions, similar patterns).\n"
    "4. Look for duplicated responsibilities or communication mismatches.\n"
    "5. Report only genuine cross-file issues."
)

_OUTPUT_FORMAT = (
    "## Output Format\n\n"
    "Return a JSON object with:\n"
    "- `files_reviewed`: list of file paths reviewed\n"
    "- `findings`: array of findings, each with: files, severity (high/medium/low),\n"
    "  category (\"design\"), subcategory (matching a checklist heading),\n"
    "  title, description, suggestion (or null)."
)


def _files_section(files: list[str]) -> str:
    file_list = "\n".join(f"- `{f}`" for f in files)
    return f"## Files to Review\n\n{file_list}"


def _metadata_section(metadata: str) -> str:
    return f"## Structural Metadata\n\n{metadata}"


def _build_system_prompt(files: list[str], metadata: str) -> str:
    return "\n\n".join([
        _ROLE,
        _files_section(files),
        _metadata_section(metadata),
        _RULES,
        _METHOD,
        _OUTPUT_FORMAT,
        DESIGN_REVIEW,
    ])


def make_python_architecture_reviewer() -> AgentDefinition:
    """Create an architecture reviewer for all Python files in the repo."""
    files = discover_files("**/*.py")
    metadata = format_analysis(analyze_files(files))
    return AgentDefinition(
        name=f"python_architecture_reviewer:{len(files)}_files",
        model="opus",
        system_prompt=_build_system_prompt(files, metadata),
        tools=["Read", "Grep"],
        output_schema=ArchitectureFindings,
    )
