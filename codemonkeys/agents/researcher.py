"""Research agent — autonomous web research with structured output."""

from __future__ import annotations

import re
from typing import Literal

from codemonkeys.core.types import AgentDefinition
from codemonkeys.prompts import (
    REPORT_FORMAT,
    RESEARCH_METHODOLOGY,
    SKILL_FORMAT,
    VERIFICATION_RULES,
)

_DEFAULT_MODEL = "opus"

OutputFormat = Literal["skill", "markdown"]

_ROLE = (
    "You are a research agent. Your job is to thoroughly investigate a topic "
    "and produce a comprehensive, actionable report. You have full autonomy "
    "to search the web, read documents, and follow reference chains."
)


def make_topic_slug(topic: str) -> str:
    """Derive a short kebab-case slug from a topic string."""
    text = re.sub(r"https?://\S+", "", topic)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    words = text.lower().split()
    words = [w for w in words if len(w) > 1]
    return "-".join(words[:5]) or "research"


def _build_system_prompt(topic: str, output_path: str, output_format: str) -> str:
    format_instructions = SKILL_FORMAT if output_format == "skill" else REPORT_FORMAT
    return "\n\n".join([
        _ROLE,
        RESEARCH_METHODOLOGY,
        VERIFICATION_RULES,
        format_instructions,
        f"## Output\n\nWrite your completed report to `{output_path}` using the Write tool.",
    ])


def make_researcher(
    topic: str,
    output_path: str,
    output_format: OutputFormat = "skill",
) -> AgentDefinition:
    """Build an AgentDefinition for autonomous web research.

    The agent uses WebSearch and WebFetch to investigate *topic*,
    then writes a structured report to *output_path* via Write.
    """
    return AgentDefinition(
        name=f"researcher:{make_topic_slug(topic)}",
        model=_DEFAULT_MODEL,
        system_prompt=_build_system_prompt(topic, output_path, output_format),
        tools=["WebFetch", "WebSearch", f"Write({output_path})"],
    )
