from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    RateLimitInfo,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from codemonkeys.core.events import (
    Event,
    RateLimitHit,
    TextOutput,
    ThinkingOutput,
)
from codemonkeys.core.runner import _estimate_cost, _extract_simple_tools, run_agent
from codemonkeys.core.types import AgentDefinition


class ReviewOutput(BaseModel):
    findings: list[str]


def _make_agent(**overrides) -> AgentDefinition:
    defaults = {
        "name": "test-agent",
        "model": "sonnet",
        "system_prompt": "You are a test agent.",
        "tools": ["Read", "Grep"],
    }
    defaults.update(overrides)
    return AgentDefinition(**defaults)


def _make_assistant_message(content=None, usage=None):
    return AssistantMessage(
        content=content or [],
        model="sonnet",
        usage=usage or {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    )


def _make_tool_use_block(name="Read", input=None):
    return ToolUseBlock(id="tool-1", name=name, input=input or {})


def _make_result_message(
    text="", structured_output=None, cost=0.01, duration_ms=500, is_error=False
):
    return ResultMessage(
        subtype="result",
        duration_ms=duration_ms,
        duration_api_ms=duration_ms,
        is_error=is_error,
        num_turns=1,
        session_id="test-session",
        total_cost_usd=cost,
        usage={"input_tokens": 1000, "output_tokens": 200, "total_tokens": 1200},
        result=text,
        structured_output=structured_output,
        stop_reason="end_turn",
    )


async def _fake_query_simple(**kwargs):
    yield _make_assistant_message(
        content=[_make_tool_use_block(name="Read", input={"file_path": "/foo.py"})],
        usage={"input_tokens": 500, "output_tokens": 100, "total_tokens": 600},
    )
    yield _make_result_message(text="All good")


async def _fake_query_structured(**kwargs):
    output = {"findings": ["unused import", "missing docstring"]}
    yield _make_result_message(
        text="",
        structured_output=output,
        cost=0.02,
        duration_ms=1200,
    )


@pytest.mark.asyncio
async def test_run_agent_basic():
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_simple):
        result = await run_agent(
            _make_agent(),
            "Review the code",
            on_event=events.append,
        )

    assert result.text == "All good"
    assert result.error is None
    assert result.cost_usd == 0.01

    event_types = [type(e).__name__ for e in events]
    assert "AgentStarted" in event_types
    assert "ToolCall" in event_types
    assert "AgentCompleted" in event_types


@pytest.mark.asyncio
async def test_run_agent_structured_output():
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_structured):
        result = await run_agent(
            _make_agent(output_schema=ReviewOutput),
            "Review the code",
            on_event=events.append,
        )

    assert result.output is not None
    assert isinstance(result.output, ReviewOutput)
    assert result.output.findings == ["unused import", "missing docstring"]
    assert result.cost_usd == 0.02


@pytest.mark.asyncio
async def test_run_agent_no_event_handler():
    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_simple):
        result = await run_agent(_make_agent(), "Review the code")

    assert result.text == "All good"


@pytest.mark.asyncio
async def test_run_agent_error_handling():
    async def _fake_query_error(**kwargs):
        yield _make_result_message(text="Something went wrong", is_error=True)

    events: list[Event] = []
    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_error):
        result = await run_agent(
            _make_agent(),
            "Do something",
            on_event=events.append,
        )

    assert result.error is not None
    event_types = [type(e).__name__ for e in events]
    assert "AgentError" in event_types


# ---------------------------------------------------------------------------
# _estimate_cost
# ---------------------------------------------------------------------------


def test_estimate_cost_sonnet() -> None:
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    cost = _estimate_cost(usage, "sonnet")
    # input: 3.0 + output: 15.0 = 18.0 USD
    assert abs(cost - 18.0) < 1e-9


def test_estimate_cost_opus() -> None:
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    cost = _estimate_cost(usage, "opus")
    # input: 5.0 + output: 25.0 = 30.0 USD
    assert abs(cost - 30.0) < 1e-9


def test_estimate_cost_haiku() -> None:
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    cost = _estimate_cost(usage, "haiku")
    # input: 1.0 + output: 5.0 = 6.0 USD
    assert abs(cost - 6.0) < 1e-9


def test_estimate_cost_unknown_model_uses_sonnet() -> None:
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    sonnet_cost = _estimate_cost(usage, "sonnet")
    unknown_cost = _estimate_cost(usage, "totally-unknown-model")
    assert abs(sonnet_cost - unknown_cost) < 1e-9


def test_estimate_cost_with_cache_tokens() -> None:
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 1_000_000,
    }
    cost = _estimate_cost(usage, "sonnet")
    # cache_read: 0.30 + cache_creation: 3.75 = 4.05 USD
    assert abs(cost - 4.05) < 1e-9


def test_estimate_cost_zero_tokens() -> None:
    usage = {"input_tokens": 0, "output_tokens": 0}
    assert _estimate_cost(usage, "opus") == 0.0


# ---------------------------------------------------------------------------
# _extract_simple_tools
# ---------------------------------------------------------------------------


def test_extract_simple_tools_bare_names() -> None:
    assert _extract_simple_tools(["Read", "Grep", "Bash"]) == ["Read", "Grep", "Bash"]


def test_extract_simple_tools_pattern_extracts_name() -> None:
    result = _extract_simple_tools(["Bash(pytest*)", "Read(src/*)"])
    assert result == ["Bash", "Read"]


def test_extract_simple_tools_deduplicates() -> None:
    result = _extract_simple_tools(["Bash(git*)", "Bash"])
    assert result.count("Bash") == 1


def test_extract_simple_tools_deduplicates_multiple_patterns() -> None:
    result = _extract_simple_tools(["Read(src/*)", "Read(tests/*)"])
    assert result.count("Read") == 1


def test_extract_simple_tools_empty() -> None:
    assert _extract_simple_tools([]) == []


def test_extract_simple_tools_mixed() -> None:
    result = _extract_simple_tools(["Grep", "Edit(src/*)", "Bash(pytest*)"])
    assert "Grep" in result
    assert "Edit" in result
    assert "Bash" in result


# ---------------------------------------------------------------------------
# ThinkingBlock and TextBlock in AssistantMessage
# ---------------------------------------------------------------------------


async def _fake_query_with_thinking(**kwargs):
    yield _make_assistant_message(
        content=[
            ThinkingBlock(thinking="I'm thinking deeply...", signature="sig-1"),
            TextBlock(text="The answer is 42."),
        ],
        usage={"input_tokens": 200, "output_tokens": 100, "total_tokens": 300},
    )
    yield _make_result_message(text="done")


@pytest.mark.asyncio
async def test_run_agent_emits_thinking_output() -> None:
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_with_thinking):
        result = await run_agent(
            _make_agent(),
            "think about it",
            on_event=events.append,
        )

    assert result.error is None
    thinking_events = [e for e in events if isinstance(e, ThinkingOutput)]
    assert len(thinking_events) == 1
    assert thinking_events[0].text == "I'm thinking deeply..."


@pytest.mark.asyncio
async def test_run_agent_emits_text_output() -> None:
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_with_thinking):
        result = await run_agent(
            _make_agent(),
            "respond",
            on_event=events.append,
        )

    text_events = [e for e in events if isinstance(e, TextOutput)]
    assert len(text_events) == 1
    assert text_events[0].text == "The answer is 42."


# ---------------------------------------------------------------------------
# RateLimitEvent
# ---------------------------------------------------------------------------


def _make_rate_limit_event(
    status: str = "allowed_warning",
    resets_at: int | None = None,
    rate_limit_type: str = "five_hour",
) -> RateLimitEvent:
    return RateLimitEvent(
        rate_limit_info=RateLimitInfo(
            status=status,
            resets_at=resets_at,
            rate_limit_type=rate_limit_type,
        ),
        uuid="test-uuid",
        session_id="test-session",
    )


async def _fake_query_rate_limit_warning(**kwargs):
    yield _make_rate_limit_event(status="allowed_warning")
    yield _make_result_message(text="done after warning")


async def _fake_query_rate_limit_rejected(**kwargs):
    # resets_at=0 → max(0 - now, 30) = 30
    yield _make_rate_limit_event(status="rejected", resets_at=0)
    yield _make_result_message(text="done after wait")


@pytest.mark.asyncio
async def test_run_agent_rate_limit_warning_emits_event() -> None:
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_rate_limit_warning):
        result = await run_agent(_make_agent(), "prompt", on_event=events.append)

    assert result.error is None
    rl_events = [e for e in events if isinstance(e, RateLimitHit)]
    assert len(rl_events) == 1
    assert rl_events[0].status == "allowed_warning"
    assert rl_events[0].wait_seconds == 0


@pytest.mark.asyncio
async def test_run_agent_rate_limit_rejected_waits() -> None:
    events: list[Event] = []

    with (
        patch("codemonkeys.core.runner.query", side_effect=_fake_query_rate_limit_rejected),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await run_agent(_make_agent(), "prompt", on_event=events.append)

    rl_events = [e for e in events if isinstance(e, RateLimitHit)]
    assert len(rl_events) == 1
    assert rl_events[0].status == "rejected"
    assert rl_events[0].wait_seconds == 30
    mock_sleep.assert_called_once_with(30)


# ---------------------------------------------------------------------------
# No ResultMessage in stream
# ---------------------------------------------------------------------------


async def _fake_query_no_result(**kwargs):
    yield _make_assistant_message()
    # Deliberately no ResultMessage


@pytest.mark.asyncio
async def test_run_agent_no_result_returns_error() -> None:
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_no_result):
        result = await run_agent(_make_agent(), "go", on_event=events.append)

    assert result.error == "No result message received from SDK"
    event_types = [type(e).__name__ for e in events]
    assert "AgentError" in event_types


# ---------------------------------------------------------------------------
# log_dir parameter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_agent_saves_patch_to_custom_log_dir(tmp_path: Path) -> None:
    with (
        patch("codemonkeys.core.runner.query", side_effect=_fake_query_simple),
        patch("codemonkeys.core.runner.generate_patch") as mock_patch,
        patch("codemonkeys.core.runner.snapshot", return_value="HEAD"),
    ):
        result = await run_agent(_make_agent(), "prompt", log_dir=tmp_path)

    assert result.error is None
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args
    assert call_args[0][0] == "HEAD"
    assert str(call_args[0][2]).startswith(str(tmp_path))


# ---------------------------------------------------------------------------
# Structured output as JSON string (not dict)
# ---------------------------------------------------------------------------


class StrOutput(BaseModel):
    value: str


async def _fake_query_structured_string(**kwargs):
    import json

    raw = json.dumps({"value": "from-string"})
    yield _make_result_message(text="", structured_output=raw, cost=0.01)


@pytest.mark.asyncio
async def test_run_agent_structured_output_as_json_string() -> None:
    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_structured_string):
        result = await run_agent(
            _make_agent(output_schema=StrOutput),
            "prompt",
        )

    assert result.output is not None
    assert isinstance(result.output, StrOutput)
    assert result.output.value == "from-string"


# ---------------------------------------------------------------------------
# Same usage doesn't re-emit TokenUpdate
# ---------------------------------------------------------------------------


async def _fake_query_same_usage_twice(**kwargs):
    usage = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
    # Two messages with identical usage
    yield _make_assistant_message(content=[], usage=usage)
    yield _make_assistant_message(content=[], usage=usage)
    yield _make_result_message(text="done")


@pytest.mark.asyncio
async def test_run_agent_no_duplicate_token_update_for_same_usage() -> None:
    events: list[Event] = []

    with patch("codemonkeys.core.runner.query", side_effect=_fake_query_same_usage_twice):
        await run_agent(_make_agent(), "prompt", on_event=events.append)

    token_updates = [e for e in events if type(e).__name__ == "TokenUpdate"]
    # Should only emit once since usage didn't change on the second message
    assert len(token_updates) == 1


# ---------------------------------------------------------------------------
# Model ID resolution
# ---------------------------------------------------------------------------


async def _fake_query_capture_model(**kwargs):
    yield _make_result_message(text="ok")


@pytest.mark.asyncio
async def test_run_agent_resolves_model_alias() -> None:
    """Model aliases like 'sonnet' are resolved to full model IDs for the SDK."""
    captured_options = []

    async def _fake_with_capture(**kwargs):
        captured_options.append(kwargs.get("options"))
        yield _make_result_message(text="ok")

    with patch("codemonkeys.core.runner.query", side_effect=_fake_with_capture):
        await run_agent(_make_agent(model="haiku"), "prompt")

    assert len(captured_options) == 1
    # The SDK receives the full model ID
    assert "haiku" in (captured_options[0].model or "")


@pytest.mark.asyncio
async def test_run_agent_passthrough_unknown_model() -> None:
    """An unrecognized model string is passed through unchanged."""
    captured_options = []

    async def _fake_with_capture(**kwargs):
        captured_options.append(kwargs.get("options"))
        yield _make_result_message(text="ok")

    with patch("codemonkeys.core.runner.query", side_effect=_fake_with_capture):
        await run_agent(_make_agent(model="custom-model-xyz"), "prompt")

    assert captured_options[0].model == "custom-model-xyz"


# ---------------------------------------------------------------------------
# SDK exception handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_agent_catches_sdk_exception(tmp_path, monkeypatch):
    """SDK exceptions become result.error instead of crashing."""

    async def _exploding_query(**kwargs):
        yield  # become an async generator
        raise Exception("Command failed with exit code 1")

    monkeypatch.setattr("codemonkeys.core.runner.query", _exploding_query)

    agent = AgentDefinition(
        name="crasher",
        model="sonnet",
        system_prompt="test",
        tools=[],
    )

    result = await run_agent(agent, "do something", log_dir=tmp_path)

    assert result.error is not None
    assert "exit code 1" in result.error
