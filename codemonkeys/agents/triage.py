"""Triage agent — presents items to the user, interprets natural-language selection."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from codemonkeys.core.events import EventHandler
from codemonkeys.core.runner import run_agent
from codemonkeys.core.types import AgentDefinition


class TriageResult(BaseModel):
    """Selected items from triage."""

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
    model: str = "haiku",
) -> AgentDefinition:
    fmt = formatter or _default_formatter
    numbered = "\n".join(f"{i}. {fmt(item)}" for i, item in enumerate(items, 1))

    return AgentDefinition(
        name="triage",
        model=model,
        system_prompt=f"""\
You are a triage agent. The user will tell you which items from the list below
they want to keep. Interpret their request — they may use natural language like
"all the high ones", "the first three and number 15", "skip the low severity stuff",
etc.

## Items

{numbered}

## Rules

- Output the 1-based indices of the items the user wants to keep.
- If the user says "all", select everything.
- If the user's intent is ambiguous, be inclusive rather than exclusive.
- Summarize what you selected and why in the summary field.""",
        tools=[],
        output_schema=TriageResult,
    )


async def run_triage(
    items: list[Any],
    *,
    on_event: EventHandler | None = None,
    formatter: Callable[[Any], str] | None = None,
    model: str = "haiku",
) -> list[Any]:
    """Interactive triage: prompt the user, interpret their selection, return selected items."""
    selection = input("\nWhich findings to fix? (or 'none' to skip) > ").strip()
    if not selection or selection.lower() == "none":
        return []

    agent = make_triage(items, formatter=formatter, model=model)
    result = await run_agent(agent, selection, on_event=on_event)

    if not isinstance(result.output, TriageResult) or not result.output.selected:
        return []

    return [items[i - 1] for i in result.output.selected]
