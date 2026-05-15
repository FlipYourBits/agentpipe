"""Core data structures."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

Severity = Literal["high", "medium", "low"]

_TOOL_SPEC_RE = re.compile(r"^(\w+)\((.+)\)$")


def parse_tool_spec(spec: str) -> tuple[str, str | None]:
    """Parse a tool spec like ``Read(codemonkeys/*)`` into ``(name, pattern)``.

    Returns ``(name, None)`` for bare tool names like ``Read``.
    """
    m = _TOOL_SPEC_RE.match(spec)
    if m:
        return m.group(1), m.group(2)
    return spec, None


def json_safe(obj: Any) -> Any:
    """Recursively convert any object to a JSON-serializable form."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, type):
        return obj.__name__
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[union-attr]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: json_safe(getattr(obj, f.name)) for f in dataclasses.fields(obj)
        }
    if hasattr(obj, "__dict__"):
        return {k: json_safe(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return repr(obj)


AgentHooks = dict[str, list[tuple[str | None, str]]]


@dataclass(frozen=True)
class AgentDefinition:
    """Immutable description of an agent to run.

    ``hooks`` maps SDK hook event names to (matcher, shell_command) pairs.
    Shell commands can use ``{field}`` placeholders interpolated from
    the hook's ``tool_input`` dict (e.g. ``{file_path}``).

    Example::

        hooks={
            "PostToolUse": [
                ("Edit", "uv run ruff check --fix {file_path}"),
                ("Write", "uv run ruff format {file_path}"),
            ],
            "Stop": [
                (None, "uv run pytest -x -q --tb=short"),
            ],
        }
    """

    name: str
    model: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    deny_hint: str | None = None
    output_schema: type[BaseModel] | None = None
    hooks: AgentHooks = field(default_factory=dict)
    max_stop_retries: int = 2


@dataclass
class TokenUsage:
    """Token accounting from a single agent run."""

    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


@dataclass
class RunResult:
    """Result returned by run_agent()."""

    output: BaseModel | None
    text: str
    usage: TokenUsage
    cost_usd: float
    duration_ms: int
    error: str | None = None
    agent_def: AgentDefinition | None = None
    events: list = field(default_factory=list)


class AuditFinding(BaseModel):
    """A single code review finding."""

    file: str
    line: int | None = None
    category: str
    severity: Severity
    title: str
    description: str
    suggestion: str | None = None


class FileReviewResult(BaseModel):
    """Structured output from a single file reviewer agent."""

    findings: list[AuditFinding]


class AuditResults(BaseModel):
    """Aggregated findings from all reviewer agents."""

    files_reviewed: list[str]
    findings: list[AuditFinding]


def make_log_dir(label: str | None = None) -> Path:
    """Create a timestamped log directory under .codemonkeys/logs/."""
    ts = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"{ts}_{label}" if label else ts
    log_dir = Path(".codemonkeys") / "logs" / name
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
