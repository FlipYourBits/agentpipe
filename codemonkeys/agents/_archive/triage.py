"""Triage agent — interprets natural-language selection over a list of items."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from codemonkeys.core.types import AgentDefinition


class TriageResult(BaseModel):
    """Structured output from the triage agent.

    ``selected`` contains 1-based indices into the original items list.
    ``summary`` is a human-readable explanation of which items were chosen and why.
    """

    select_all: bool = False
    selected: list[int]
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


def make_triage(
    items: list[Any],
    *,
    formatter: Callable[[Any], str] | None = None,
) -> AgentDefinition:
    """Build an AgentDefinition that interprets a natural-language selection over *items*.

    The item list is embedded in the system prompt at construction time, so
    *items* must be fully populated before calling this function.
    *formatter* converts each item to a display string; defaults to
    ``_default_formatter``.
    """
    fmt = formatter or _default_formatter
    numbered = "\n".join(f"{i}. {fmt(item)}" for i, item in enumerate(items, 1))

    return AgentDefinition(
        name="triage",
        model="haiku",
        system_prompt=f"""\
You are a triage agent. The user will tell you which items from the list below
they want to keep. Interpret their request — they may use natural language like
"all the high ones", "the first three and number 15", "skip the low severity stuff",
etc.

## Items

{numbered}

## Rules

- If the user wants everything, set select_all to true and leave selected empty.
- Otherwise, set select_all to false and output the 1-based indices of the
  items the user wants to keep in selected.
- If the user's intent is ambiguous, be inclusive rather than exclusive.
- Summarize what you selected and why in the summary field.""",
        tools=[],
        output_schema=TriageResult,
    )
