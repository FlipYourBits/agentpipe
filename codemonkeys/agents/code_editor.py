"""General-purpose code editor agent — single or multi-file."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, get_args

from codemonkeys.agents.code_reviewer import get_language_config
from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import ENGINEERING_GUIDELINES

TaskType = Literal["fix", "feat", "refactor", "test", "docs"]

_DEFAULT_MODEL = "sonnet"

_WRITABLE_TYPES: set[TaskType] = {"feat", "test", "docs"}

_ROLE = (
    "You are a code editor. You receive a specific task and apply "
    "changes to the target file(s). Follow the task instructions precisely."
)


def _rules(file_paths: list[str]) -> str:
    if len(file_paths) == 1:
        scope = f"Only edit `{file_paths[0]}` — do not touch other files."
    else:
        listed = ", ".join(f"`{f}`" for f in file_paths)
        scope = f"Only edit these files: {listed} — do not touch other files."
    return (
        "## Rules\n\n"
        f"- {scope}\n"
        "- Do not push, commit, or modify git state.\n"
        "- Do not introduce new bugs while making changes.\n"
        "- If the task is unclear, make the safest reasonable interpretation."
    )


def _guidelines(file_paths: list[str]) -> str:
    sections = [
        "## Guidelines\n\nFollow these when making changes.",
        ENGINEERING_GUIDELINES,
    ]
    seen: set[str] = set()
    for fp in file_paths:
        ext = Path(fp).suffix
        if ext in seen:
            continue
        seen.add(ext)
        _, lang_guidelines = get_language_config(ext)
        if lang_guidelines:
            sections.append(lang_guidelines)
    return "\n\n".join(sections)


def _build_system_prompt(file_paths: list[str], task: str) -> str:
    return "\n\n".join([
        _ROLE,
        f"## Task\n\n{task}",
        _rules(file_paths),
        _guidelines(file_paths),
    ])


def _build_tools(
    file_paths: list[str], task_type: TaskType, read_paths: list[str] | None,
) -> list[str]:
    tools: list[str] = []
    for fp in file_paths:
        tools.append(f"Read({fp})")
    for path in (read_paths or []):
        if path not in file_paths:
            tools.append(f"Read({path})")
    for fp in file_paths:
        tools.append(f"Edit({fp})")
    if task_type in _WRITABLE_TYPES:
        for fp in file_paths:
            tools.append(f"Write({fp})")
    return tools


def _build_name(file_paths: list[str], task_type: str) -> str:
    if len(file_paths) == 1:
        return f"code_editor:{task_type}:{Path(file_paths[0]).name}"
    return f"code_editor:{task_type}:{len(file_paths)}_files"


def make_code_editor(
    file_path: str | list[str],
    task: str,
    task_type: TaskType,
    *,
    read_paths: list[str] | None = None,
) -> AgentDefinition:
    """Build an AgentDefinition that edits file(s) based on a task description.

    *file_path* can be a single path or a list for cross-file edits.

    Tool selection adapts to *task_type*:
    - fix, refactor: Read + Edit (files exist)
    - feat, test, docs: Read + Edit + Write (may create new files)

    Extra *read_paths* are added as Read-only tools for context.

    Language-specific guidelines are auto-detected from file extensions.
    For multi-file calls with mixed extensions, all matching guidelines
    are included.
    """
    valid = set(get_args(TaskType))
    if task_type not in valid:
        raise ValueError(f"Invalid task_type {task_type!r}, must be one of {valid}")

    file_paths = [file_path] if isinstance(file_path, str) else list(file_path)

    return AgentDefinition(
        name=_build_name(file_paths, task_type),
        model=_DEFAULT_MODEL,
        system_prompt=_build_system_prompt(file_paths, task),
        tools=_build_tools(file_paths, task_type, read_paths),
    )
