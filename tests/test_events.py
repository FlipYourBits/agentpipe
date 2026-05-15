import time

from codemonkeys.core.events import (
    AgentCompleted,
    AgentError,
    AgentStarted,
    CheckResult,
    Event,
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
from codemonkeys.core.types import RunResult, TokenUsage


def test_event_base_fields():
    e = AgentStarted(agent_name="reviewer", timestamp=1000.0, model="sonnet")
    assert e.agent_name == "reviewer"
    assert e.timestamp == 1000.0
    assert e.model == "sonnet"


def test_tool_call_event():
    e = ToolCall(
        agent_name="reviewer",
        timestamp=time.time(),
        tool_name="Read",
        tool_input={"file_path": "/foo.py"},
    )
    assert e.tool_name == "Read"
    assert e.tool_input["file_path"] == "/foo.py"


def test_tool_denied_event():
    e = ToolDenied(
        agent_name="reviewer",
        timestamp=time.time(),
        tool_name="Bash",
        command="rm -rf /",
    )
    assert e.tool_name == "Bash"
    assert e.command == "rm -rf /"


def test_token_update_event():
    usage = TokenUsage(input_tokens=500, output_tokens=100)
    e = TokenUpdate(
        agent_name="reviewer",
        timestamp=time.time(),
        usage=usage,
        cost_usd=0.005,
    )
    assert e.usage.input_tokens == 500
    assert e.cost_usd == 0.005


def test_agent_completed_event():
    usage = TokenUsage(input_tokens=1000, output_tokens=200)
    result = RunResult(
        output=None, text="done", usage=usage, cost_usd=0.01, duration_ms=500
    )
    e = AgentCompleted(
        agent_name="reviewer",
        timestamp=time.time(),
        result=result,
    )
    assert e.result.text == "done"


def test_agent_error_event():
    e = AgentError(
        agent_name="reviewer",
        timestamp=time.time(),
        error="Rate limit exceeded",
    )
    assert e.error == "Rate limit exceeded"


def test_event_handler_type():
    """EventHandler is just a callable that takes an Event."""
    received: list[Event] = []

    def handler(event: Event) -> None:
        received.append(event)

    h: EventHandler = handler
    h(AgentStarted(agent_name="x", timestamp=0.0, model="sonnet"))
    assert len(received) == 1


# ---------------------------------------------------------------------------
# Additional event types not in the original test file
# ---------------------------------------------------------------------------


def test_thinking_output_event():
    e = ThinkingOutput(agent_name="thinker", timestamp=time.time(), text="I'm pondering...")
    assert e.agent_name == "thinker"
    assert e.text == "I'm pondering..."


def test_text_output_event():
    e = TextOutput(agent_name="writer", timestamp=time.time(), text="Hello, world!")
    assert e.agent_name == "writer"
    assert e.text == "Hello, world!"


def test_raw_message_event():
    e = RawMessage(
        agent_name="logger",
        timestamp=time.time(),
        message_type="AssistantMessage",
        data={"content": [], "model": "sonnet"},
    )
    assert e.message_type == "AssistantMessage"
    assert e.data["model"] == "sonnet"


def test_check_result_passed():
    e = CheckResult(
        agent_name="checker",
        timestamp=time.time(),
        hook_event="PostToolUse",
        command="ruff check .",
        passed=True,
        output="All checks passed",
    )
    assert e.hook_event == "PostToolUse"
    assert e.passed is True
    assert e.output == "All checks passed"


def test_check_result_failed():
    e = CheckResult(
        agent_name="checker",
        timestamp=time.time(),
        hook_event="Stop",
        command="pytest",
        passed=False,
        output="1 test failed",
    )
    assert e.passed is False
    assert e.command == "pytest"


def test_rate_limit_hit_event():
    e = RateLimitHit(
        agent_name="runner",
        timestamp=time.time(),
        rate_limit_type="five_hour",
        status="rejected",
        wait_seconds=30,
    )
    assert e.rate_limit_type == "five_hour"
    assert e.status == "rejected"
    assert e.wait_seconds == 30


def test_rate_limit_hit_warning():
    e = RateLimitHit(
        agent_name="runner",
        timestamp=time.time(),
        rate_limit_type="seven_day",
        status="allowed_warning",
        wait_seconds=0,
    )
    assert e.wait_seconds == 0
    assert e.status == "allowed_warning"


# ---------------------------------------------------------------------------
# EventCollector
# ---------------------------------------------------------------------------


def test_event_collector_starts_empty():
    collector = EventCollector()
    assert collector.events == []


def test_event_collector_accumulates_events():
    collector = EventCollector()
    e1 = AgentStarted(agent_name="a", timestamp=1.0, model="sonnet")
    e2 = TextOutput(agent_name="a", timestamp=2.0, text="done")
    collector.handle(e1)
    collector.handle(e2)
    assert len(collector.events) == 2
    assert collector.events[0] is e1
    assert collector.events[1] is e2


def test_event_collector_handle_preserves_order():
    collector = EventCollector()
    events = [
        AgentStarted(agent_name="a", timestamp=float(i), model="sonnet")
        for i in range(5)
    ]
    for e in events:
        collector.handle(e)
    assert collector.events == events
