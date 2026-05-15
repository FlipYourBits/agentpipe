"""File logger — writes events as JSONL and run metadata."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, Iterator

from codemonkeys.core.events import Event, EventHandler
from codemonkeys.core.types import AgentDefinition, json_safe
from codemonkeys.display.stdout import fan_out, make_stdout_printer


class FileLogger:
    """Writes events as JSON lines to a file.

    Usage:
        logger = FileLogger("run.jsonl")
        result = await run_agent(agent, prompt, on_event=logger.handle)
        logger.close()
    """

    def __init__(self, path: str | Path) -> None:
        self._file: IO[str] = open(path, "a")

    def handle(self, event: Event) -> None:
        data = json_safe(event)
        data["_type"] = type(event).__name__
        self._file.write(json.dumps(data, default=str) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()


def save_run_meta(
    log_dir: Path, name: str, agent: AgentDefinition, prompt: str
) -> None:
    """Write agent definition and prompt alongside the event log."""
    meta: dict[str, Any] = {
        "agent_name": agent.name,
        "model": agent.model,
        "system_prompt": agent.system_prompt,
        "tools": agent.tools,
        "prompt": prompt,
    }
    path = log_dir / f"{name}_meta.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_run_meta(path: Path) -> dict[str, Any]:
    """Read a metadata file written by save_run_meta."""
    return json.loads(path.read_text(encoding="utf-8"))


@contextmanager
def logged(log_dir: Path, name: str, printer: EventHandler | None = None) -> Iterator[EventHandler]:
    if printer is None:
        printer = make_stdout_printer()
    logger = FileLogger(log_dir / f"{name}_events.jsonl")
    try:
        yield fan_out(printer, logger.handle)
    finally:
        logger.close()
