"""Tests for InteractiveSession in codemonkeys/core/runner.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
)

from codemonkeys.core.runner import InteractiveSession
from codemonkeys.core.types import AgentDefinition, RunResult


class SampleOutput(BaseModel):
    answer: str


def _make_agent(**overrides) -> AgentDefinition:
    defaults = {
        "name": "test-interactive",
        "model": "sonnet",
        "system_prompt": "You are a test agent.",
        "tools": ["Read", "Grep"],
        "output_schema": SampleOutput,
    }
    defaults.update(overrides)
    return AgentDefinition(**defaults)


def _make_result_message(
    text="done", structured_output=None, cost=0.01, duration_ms=500
):
    return ResultMessage(
        subtype="result",
        duration_ms=duration_ms,
        duration_api_ms=duration_ms,
        is_error=False,
        num_turns=1,
        session_id="test-session",
        total_cost_usd=cost,
        usage={"input_tokens": 1000, "output_tokens": 200, "total_tokens": 1200},
        result=text,
        structured_output=structured_output,
        stop_reason="end_turn",
    )


def test_interactive_session_init() -> None:
    agent = _make_agent()
    session = InteractiveSession(agent)
    assert session._agent is agent
    assert session.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_interactive_session_send_returns_run_result() -> None:
    agent = _make_agent()
    result_msg = _make_result_message(
        text="here is the answer",
        structured_output={"answer": "42"},
        cost=0.05,
    )

    mock_client = AsyncMock()
    mock_client.query = AsyncMock()

    async def fake_receive():
        yield result_msg

    mock_client.receive_response = fake_receive

    session = InteractiveSession(agent)
    session._client = mock_client
    session._connected = True
    result = await session.send("hello")

    assert isinstance(result, RunResult)
    assert isinstance(result.output, SampleOutput)
    assert result.output.answer == "42"
    assert result.cost_usd == 0.05


@pytest.mark.asyncio
async def test_interactive_session_accumulates_cost() -> None:
    agent = _make_agent()

    msg1 = _make_result_message(cost=0.03)
    msg2 = _make_result_message(cost=0.07)

    mock_client = AsyncMock()
    mock_client.query = AsyncMock()
    call_count = 0

    async def fake_receive():
        nonlocal call_count
        call_count += 1
        yield msg1 if call_count == 1 else msg2

    mock_client.receive_response = fake_receive

    session = InteractiveSession(agent)
    session._client = mock_client
    session._connected = True

    r1 = await session.send("first")
    r2 = await session.send("second")

    assert r1.cost_usd == 0.03
    assert r2.cost_usd == 0.07
    assert session.total_cost_usd == pytest.approx(0.10)


@pytest.mark.asyncio
async def test_interactive_session_context_manager() -> None:
    agent = _make_agent()

    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()

    with patch(
        "codemonkeys.core.runner.ClaudeSDKClient", return_value=mock_client
    ):
        session = InteractiveSession(agent)
        async with session:
            assert session._connected
        mock_client.connect.assert_awaited_once()
        mock_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_interactive_session_emits_events() -> None:
    agent = _make_agent()
    result_msg = _make_result_message(text="done", structured_output={"answer": "yes"})
    assistant_msg = AssistantMessage(
        content=[TextBlock(text="thinking aloud")],
        model="sonnet",
        usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    )

    mock_client = AsyncMock()
    mock_client.query = AsyncMock()

    async def fake_receive():
        yield assistant_msg
        yield result_msg

    mock_client.receive_response = fake_receive

    events = []

    session = InteractiveSession(agent, on_event=lambda e: events.append(e))
    session._client = mock_client
    session._connected = True
    await session.send("hello")

    event_types = [type(e).__name__ for e in events]
    assert "TextOutput" in event_types
    assert "RawMessage" in event_types
    assert "TokenUpdate" in event_types


@pytest.mark.asyncio
async def test_interactive_session_send_without_connect_raises() -> None:
    agent = _make_agent()
    session = InteractiveSession(agent)
    with pytest.raises(RuntimeError, match="not connected"):
        await session.send("hello")


@pytest.mark.asyncio
async def test_interactive_session_send_no_result_message() -> None:
    """If no ResultMessage is received, send() returns an error RunResult."""
    agent = _make_agent()
    mock_client = AsyncMock()
    mock_client.query = AsyncMock()

    async def fake_receive():
        return
        yield  # make it an async generator

    mock_client.receive_response = fake_receive

    session = InteractiveSession(agent)
    session._client = mock_client
    session._connected = True
    result = await session.send("hello")

    assert result.error is not None
    assert "No result message" in result.error
