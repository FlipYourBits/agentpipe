"""File-based event printer — writes human-readable agent activity to a log file."""

from __future__ import annotations

from pathlib import Path

from codemonkeys.core.events import (
    AgentCompleted,
    AgentError,
    AgentStarted,
    CheckResult,
    Event,
    EventHandler,
    RateLimitHit,
    ThinkingOutput,
    ToolCall,
    ToolDenied,
    TokenUpdate,
)
from codemonkeys.display.formatting import format_tool_call


def make_file_printer(path: Path) -> EventHandler:
    """Return an event handler that writes formatted agent activity to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a", encoding="utf-8")  # noqa: SIM115

    def _write(line: str) -> None:
        handle.write(line + "\n")
        handle.flush()

    def _handler(event: Event) -> None:
        name = event.agent_name

        if isinstance(event, AgentStarted):
            _write(f"{name} started [{event.model}]")

        elif isinstance(event, ThinkingOutput):
            text = event.text[:500] if event.text else ""
            _write(f"  {name} thinking: {text}")

        elif isinstance(event, ToolCall):
            detail = format_tool_call(event.tool_name, event.tool_input)
            _write(f"  {name} -> {detail}")

        elif isinstance(event, ToolDenied):
            _write(f"  {name} DENIED: {event.tool_name}({event.command[:100]})")

        elif isinstance(event, CheckResult):
            label = "PASS" if event.passed else "FAIL"
            _write(f"  {name} check {label}: {event.command[:100]}")
            if event.output and not event.passed:
                for line in event.output.splitlines()[:5]:
                    _write(f"    {line}")

        elif isinstance(event, TokenUpdate):
            u = event.usage
            _write(
                f"  {name} ${event.cost_usd:.4f} "
                f"({u.input_tokens} in + {u.cache_read_tokens} cache_read "
                f"+ {u.cache_creation_tokens} cache_write / {u.output_tokens} out)"
            )

        elif isinstance(event, RateLimitHit):
            if event.status == "rejected":
                _write(f"  {name} rate limited ({event.rate_limit_type}) — waiting {event.wait_seconds}s")

        elif isinstance(event, AgentCompleted):
            r = event.result
            secs = r.duration_ms / 1000
            duration = f"{secs / 60:.1f}m" if secs >= 60 else f"{secs:.1f}s"
            _write(f"{name} done — ${r.cost_usd:.4f} in {duration}")

        elif isinstance(event, AgentError):
            _write(f"{name} ERROR: {event.error}")

    return _handler
