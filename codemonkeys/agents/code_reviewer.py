"""Per-file code reviewer agent — read-only review with structured findings."""

from __future__ import annotations

import re
from pathlib import Path

from codemonkeys.core.types import AgentDefinition, FileReviewResult
from codemonkeys.prompts import (
    CODE_REVIEW,
    DESIGN_REVIEW,
    PERFORMANCE_REVIEW,
    PYTHON_GUIDELINES,
    RESILIENCE_REVIEW,
    SECURITY_REVIEW,
)


DEFAULT_REVIEWER_MODEL = "sonnet"

# Private registry mapping file extension -> (language name, guidelines).
# Use register_guidelines() to add entries for additional languages.
_GUIDELINES: dict[str, tuple[str, str]] = {
    ".py": ("Python", PYTHON_GUIDELINES),
}


def register_guidelines(ext: str, language: str, guidelines: str) -> None:
    """Register language-specific guidelines for a file extension."""
    _GUIDELINES[ext] = (language, guidelines)


def get_language_config(ext: str) -> tuple[str, str | None]:
    """Look up language name and guidelines by extension."""
    if (entry := _GUIDELINES.get(ext)) is not None:
        return entry
    return "general", None


def _validate_file_path(file_path: str) -> None:
    """Reject paths containing newlines or control characters that could corrupt prompts."""
    if re.search(r"[\x00-\x1f]", file_path):
        raise ValueError(f"File path contains control characters: {file_path!r}")


_OUTPUT_INSTRUCTIONS = (
    "## Output Format\n\n"
    "Return a JSON object with a `findings` array. Each finding has:\n"
    "- `file`: the file path being reviewed\n"
    "- `line`: line number where the issue occurs (or null if file-wide)\n"
    "- `category`: one of: naming, function_design, class_design, documentation, "
    "error_handling, code_structure, complexity, security, resilience, performance, design\n"
    "- `severity`: high, medium, or low\n"
    "- `title`: short one-line summary of the issue\n"
    "- `description`: detailed explanation of the problem\n"
    "- `suggestion`: how to fix it (or null if obvious)\n\n"
    "If the file has no issues, return an empty findings array.\n"
    "Only report findings at 80%+ confidence."
)


def _role(language: str) -> str:
    return (
        f"You are a {language} code reviewer. Your job is to read a file and report "
        "any issues you find as structured findings. You are read-only — do not "
        "edit, create, or delete any files."
    )


def _rules(file_path: str) -> str:
    return (
        "## Rules\n\n"
        f"- Only read `{file_path}` — do not read, edit, or touch other files.\n"
        "- Do not modify, create, or delete any files.\n"
        "- Do not run commands, install packages, or modify git state.\n"
        "- Infer context from the target file alone.\n"
        "- Report issues, do not fix them."
    )


def _checklists() -> str:
    return "\n\n".join([
        "## Review Checklists\n\nEvaluate the file against each checklist below.",
        CODE_REVIEW,
        SECURITY_REVIEW,
        RESILIENCE_REVIEW,
        PERFORMANCE_REVIEW,
        DESIGN_REVIEW,
    ])


def _build_system_prompt(file_path: str, language: str, guidelines: str | None) -> str:
    sections = [
        _role(language),
        _rules(file_path),
        _checklists(),
    ]
    if guidelines:
        sections.append(guidelines)
    sections.append(_OUTPUT_INSTRUCTIONS)
    return "\n\n".join(sections)


def make_code_reviewer(file_path: str) -> AgentDefinition:
    """Build an AgentDefinition that reviews a single file (read-only).

    Language and guidelines are auto-detected from the file extension.
    """
    _validate_file_path(file_path)
    ext = Path(file_path).suffix
    language, guidelines = get_language_config(ext)
    return AgentDefinition(
        name=f"code_reviewer:{Path(file_path).name}",
        model=DEFAULT_REVIEWER_MODEL,
        system_prompt=_build_system_prompt(file_path, language, guidelines),
        tools=[f"Read({file_path})"],
        deny_hint="You are a read-only reviewer — do not edit or create files.",
        output_schema=FileReviewResult,
    )
