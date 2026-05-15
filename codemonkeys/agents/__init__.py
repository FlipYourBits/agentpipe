"""Agent factory functions and reviewer registry."""

from __future__ import annotations

from typing import Callable

from codemonkeys.agents.code_editor import make_code_editor
from codemonkeys.agents.code_reviewer import (
    make_code_reviewer,
    register_guidelines,
)
from codemonkeys.core.types import AgentDefinition

REVIEWERS: dict[str, Callable[[str], AgentDefinition]] = {
    ".py": make_code_reviewer,
}


def get_reviewer(ext: str) -> Callable[[str], AgentDefinition] | None:
    """Look up a reviewer factory by file extension. Returns None if no reviewer is registered."""
    return REVIEWERS.get(ext)


def register_reviewer(ext: str, factory: Callable[[str], AgentDefinition]) -> None:
    """Register a reviewer factory for a file extension (e.g. ``".js"``)."""
    REVIEWERS[ext] = factory


__all__ = [
    "get_reviewer",
    "make_code_editor",
    "make_code_reviewer",
    "register_guidelines",
    "register_reviewer",
]
