"""Orchestration — interactive workflows that combine agents with user I/O."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable

from codemonkeys.agents.triage import TriageResult, make_triage
from codemonkeys.core.events import EventHandler
from codemonkeys.core.runner import run_agent

_log = logging.getLogger(__name__)


async def _prompt_user(prompt: str) -> str:
    """Read user input without blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def run_triage(
    items: list[Any],
    *,
    prompt: str = "Which items to keep? (or 'none' to skip)",
    on_event: EventHandler | None = None,
    formatter: Callable[[Any], str] | None = None,
    log_dir: Path | None = None,
) -> list[Any]:
    """Interactive triage: prompt the user, interpret their selection, return selected items."""
    selection = (await _prompt_user(f"\n{prompt} > ")).strip()
    if not selection or selection.lower() == "none":
        return []

    agent = make_triage(items, formatter=formatter)
    result = await run_agent(agent, selection, on_event=on_event, log_dir=log_dir)

    if not isinstance(result.output, TriageResult):
        _log.warning(
            "triage agent returned unexpected output (error=%s); treating as empty selection",
            result.error,
        )
        return []

    if result.output.select_all:
        return list(items)

    if not result.output.selected:
        return []

    valid = [i for i in result.output.selected if 1 <= i <= len(items)]
    return [items[i - 1] for i in valid]
