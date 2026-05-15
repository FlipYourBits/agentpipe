"""Agent runner — thin wrapper around claude_agent_sdk.query()."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    RateLimitEvent,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    query,
)
from claude_agent_sdk.types import SystemPromptFile

from codemonkeys.core.events import (
    AgentCompleted,
    AgentError,
    AgentStarted,
    CheckResult,
    EventCollector,
    EventHandler,
    RateLimitHit,
    RawMessage,
    TextOutput,
    ThinkingOutput,
    ToolCall,
    ToolDenied,
    TokenUpdate,
)
from codemonkeys.core.hooks import (
    build_check_hooks,
    build_permission_hooks,
    merge_hooks,
)
from codemonkeys.core.sandbox import restrict
from codemonkeys.core.diff import generate_patch, snapshot
from codemonkeys.core.types import (
    AgentDefinition,
    RunResult,
    TokenUsage,
    json_safe,
    make_log_dir,
    parse_tool_spec,
)

_log = logging.getLogger(__name__)

_MODEL_IDS: dict[str, str] = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

_PRICING: dict[str, dict[str, float]] = {
    "opus": {"input": 5.0, "output": 25.0, "cache_read": 0.50, "cache_creation": 6.25},
    "sonnet": {
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.30,
        "cache_creation": 3.75,
    },
    "haiku": {"input": 1.0, "output": 5.0, "cache_read": 0.10, "cache_creation": 1.25},
}


def _estimate_cost(usage: dict[str, int], model: str) -> float:
    rates = _PRICING.get(model, _PRICING["sonnet"])
    m = 1_000_000
    return (
        usage.get("input_tokens", 0) * rates["input"] / m
        + usage.get("output_tokens", 0) * rates["output"] / m
        + usage.get("cache_read_input_tokens", 0) * rates["cache_read"] / m
        + usage.get("cache_creation_input_tokens", 0) * rates["cache_creation"] / m
    )


_json_safe = json_safe


Emit = Any  # (event) -> None


def _extract_simple_tools(tools: list[str]) -> list[str]:
    """Get tool names suitable for SDK allowed_tools (no Tool(pattern) specs)."""
    result: list[str] = []
    for t in tools:
        name, _ = parse_tool_spec(t)
        if name not in result:
            result.append(name)
    return result


_STRUCTURED_OUTPUT_STOP = (
    "\n\nAfter submitting your structured output, stop immediately."
    " Do not produce any additional text or summary."
)

_SYSTEM_PROMPT_FILE_THRESHOLD = 100_000


def _build_options(agent: AgentDefinition, emit: Emit) -> ClaudeAgentOptions:
    """Build SDK options from an AgentDefinition."""
    output_format: dict[str, Any] | None = None
    if agent.output_schema:
        output_format = {
            "type": "json_schema",
            "schema": agent.output_schema.model_json_schema(),
        }

    def _on_deny(tool_name: str, command: str) -> None:
        emit(
            ToolDenied(
                agent_name=agent.name,
                timestamp=time.time(),
                tool_name=tool_name,
                command=command,
            )
        )

    def _on_check(hook_event: str, command: str, passed: bool, output: str) -> None:
        emit(
            CheckResult(
                agent_name=agent.name,
                timestamp=time.time(),
                hook_event=hook_event,
                command=command,
                passed=passed,
                output=output,
            )
        )

    sdk_tools = _extract_simple_tools(agent.tools)
    allowed = list(sdk_tools)
    if output_format:
        allowed.append("StructuredOutput")

    hooks = merge_hooks(
        build_permission_hooks(agent.tools, on_deny=_on_deny, deny_hint=agent.deny_hint),
        build_check_hooks(
            agent.hooks,
            agent_name=agent.name,
            on_check=_on_check,
            max_stop_retries=agent.max_stop_retries,
        )
        if agent.hooks
        else None,
    )

    system_prompt_text = agent.system_prompt
    if output_format:
        system_prompt_text += _STRUCTURED_OUTPUT_STOP

    system_prompt: str | SystemPromptFile
    if len(system_prompt_text) > _SYSTEM_PROMPT_FILE_THRESHOLD:
        sp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            prefix="codemonkeys_sp_",
            delete=False,
        )
        sp_file.write(system_prompt_text)
        sp_file.close()
        system_prompt = SystemPromptFile(type="file", path=sp_file.name)
    else:
        system_prompt = system_prompt_text

    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=_MODEL_IDS.get(agent.model, agent.model),
        permission_mode="dontAsk",
        tools=sdk_tools,
        allowed_tools=allowed,
        hooks=hooks,
        output_format=output_format,
        mcp_servers={},
        plugins=[],
        setting_sources=[],
        skills=[],
    )


async def _process_message(
    message: Any, agent: AgentDefinition, emit: Emit, state: dict[str, Any]
) -> None:
    """Process a single SDK message, updating *state* in place."""
    emit(
        RawMessage(
            agent_name=agent.name,
            timestamp=time.time(),
            message_type=type(message).__name__,
            data=_json_safe(message),
        )
    )

    if isinstance(message, AssistantMessage):
        usage = message.usage or {}
        state["usage"] = TokenUsage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
        )
        state["cost"] = _estimate_cost(usage, agent.model)

        for block in message.content:
            if isinstance(block, ThinkingBlock):
                emit(
                    ThinkingOutput(
                        agent_name=agent.name,
                        timestamp=time.time(),
                        text=block.thinking or "",
                    )
                )
            elif isinstance(block, TextBlock):
                emit(
                    TextOutput(
                        agent_name=agent.name,
                        timestamp=time.time(),
                        text=block.text or "",
                    )
                )
            elif isinstance(block, ToolUseBlock):
                emit(
                    ToolCall(
                        agent_name=agent.name,
                        timestamp=time.time(),
                        tool_name=block.name,
                        tool_input=block.input or {},
                    )
                )

        if state["usage"] != state.get("last_emitted_usage"):
            emit(
                TokenUpdate(
                    agent_name=agent.name,
                    timestamp=time.time(),
                    usage=state["usage"],
                    cost_usd=state["cost"],
                )
            )
            state["last_emitted_usage"] = state["usage"]

    elif isinstance(message, RateLimitEvent):
        info = message.rate_limit_info
        resets_at = info.resets_at or 0
        wait = max(resets_at - int(time.time()), 30) if info.status == "rejected" else 0
        emit(
            RateLimitHit(
                agent_name=agent.name,
                timestamp=time.time(),
                rate_limit_type=info.rate_limit_type or "unknown",
                status=info.status,
                wait_seconds=wait,
            )
        )
        if info.status == "rejected":
            _log.warning("Rate limited (%s), waiting %ds", info.rate_limit_type, wait)
            await asyncio.sleep(wait)

    elif isinstance(message, ResultMessage):
        state["result"] = message


def _build_run_result(
    agent: AgentDefinition,
    state: dict[str, Any],
    elapsed_ms: int,
    events: list,
) -> RunResult:
    """Build a RunResult from accumulated stream state."""
    last_result: ResultMessage | None = state.get("result")

    if last_result is None:
        return RunResult(
            output=None,
            text="",
            usage=state.get("usage", TokenUsage(input_tokens=0, output_tokens=0)),
            cost_usd=0.0,
            duration_ms=elapsed_ms,
            error=state.get("error", "No result message received from SDK"),
            agent_def=agent,
            events=events,
        )

    final_usage_raw = last_result.usage or {}
    final_usage = TokenUsage(
        input_tokens=final_usage_raw.get("input_tokens", 0),
        output_tokens=final_usage_raw.get("output_tokens", 0),
        cache_read_tokens=final_usage_raw.get("cache_read_input_tokens", 0),
        cache_creation_tokens=final_usage_raw.get("cache_creation_input_tokens", 0),
    )

    parsed_output = None
    if agent.output_schema and last_result.structured_output is not None:
        raw = last_result.structured_output
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = None
        if isinstance(raw, dict):
            parsed_output = agent.output_schema.model_validate(raw)

    error = None
    if last_result.is_error:
        error = last_result.result or "Agent returned an error"

    return RunResult(
        output=parsed_output,
        text=last_result.result or "",
        usage=final_usage,
        cost_usd=last_result.total_cost_usd or 0.0,
        duration_ms=last_result.duration_ms or elapsed_ms,
        error=error,
        agent_def=agent,
        events=events,
    )


async def run_agent(
    agent: AgentDefinition,
    prompt: str,
    on_event: EventHandler | None = None,
    log_dir: Path | None = None,
) -> RunResult:
    """Run a single agent and return its result."""
    restrict(".")
    collector = EventCollector()

    def emit(event: Any) -> None:
        collector.handle(event)
        if on_event:
            on_event(event)

    emit(AgentStarted(agent_name=agent.name, timestamp=time.time(), model=agent.model))
    start_time = time.monotonic()

    ref = snapshot()

    options = _build_options(agent, emit)
    sp_temp: str | None = None
    if (
        isinstance(options.system_prompt, dict)
        and options.system_prompt.get("type") == "file"
    ):
        sp_temp = options.system_prompt.get("path")
    state: dict[str, Any] = {}

    try:
        async for message in query(prompt=prompt, options=options):
            await _process_message(message, agent, emit, state)
    except Exception as exc:
        state["error"] = str(exc)
    finally:
        if sp_temp:
            Path(sp_temp).unlink(missing_ok=True)

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    events_snapshot = list(collector.events)
    result = _build_run_result(agent, state, elapsed_ms, events_snapshot)

    if result.error:
        emit(
            AgentError(agent_name=agent.name, timestamp=time.time(), error=result.error)
        )
    else:
        emit(
            AgentCompleted(agent_name=agent.name, timestamp=time.time(), result=result)
        )

    try:
        dest = log_dir if log_dir else make_log_dir()
        name = re.sub(r"[^\w\-.]", "_", agent.name)
        generate_patch(ref, [], dest / f"{name}_changes.patch")
    except Exception:
        _log.debug("Failed to save changes patch for %s", agent.name, exc_info=True)

    return result


class InteractiveSession:
    """Stateful multi-turn agent session wrapping ClaudeSDKClient.

    Provides the same event tracking, cost accounting, and structured output
    parsing as :func:`run_agent`, but for interactive sessions where the caller
    sends follow-up messages.

    Usage::

        async with InteractiveSession(agent, on_event=handler) as session:
            r1 = await session.send("first prompt")
            r2 = await session.send("follow-up")
        print(session.total_cost_usd)
    """

    def __init__(
        self,
        agent: AgentDefinition,
        on_event: EventHandler | None = None,
    ) -> None:
        self._agent = agent
        self._on_event = on_event
        self._collector = EventCollector()
        self.total_cost_usd: float = 0.0
        self._options = _build_options(agent, self._emit)
        self._client: ClaudeSDKClient | None = None
        self._connected: bool = False

    async def __aenter__(self) -> InteractiveSession:
        restrict(".")
        self._client = ClaudeSDKClient(options=self._options)
        await self._client.connect()
        self._connected = True
        self._emit(
            AgentStarted(
                agent_name=self._agent.name,
                timestamp=time.time(),
                model=self._agent.model,
            )
        )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client:
            await self._client.disconnect()
            self._connected = False

    async def send(self, prompt: str) -> RunResult:
        """Send a message and return the result for this turn."""
        if not self._connected or self._client is None:
            raise RuntimeError(
                "Session not connected — use 'async with' or call __aenter__"
            )

        turn_start = len(self._collector.events)
        start_time = time.monotonic()
        await self._client.query(prompt)

        state: dict[str, Any] = {}
        async for message in self._client.receive_response():
            await _process_message(message, self._agent, self._emit, state)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        events_snapshot = list(self._collector.events[turn_start:])
        result = _build_run_result(self._agent, state, elapsed_ms, events_snapshot)

        if result.error:
            self._emit(
                AgentError(
                    agent_name=self._agent.name,
                    timestamp=time.time(),
                    error=result.error,
                )
            )
        else:
            self._emit(
                AgentCompleted(
                    agent_name=self._agent.name,
                    timestamp=time.time(),
                    result=result,
                )
            )

        self.total_cost_usd += result.cost_usd
        return result

    def _emit(self, event: Any) -> None:
        """Add event to collector and forward to handler if set."""
        self._collector.handle(event)
        if self._on_event:
            self._on_event(event)
