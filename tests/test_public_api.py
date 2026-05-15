from __future__ import annotations


def test_top_level_imports() -> None:
    """Everything needed is importable from the top-level package."""
    import codemonkeys.core

    assert hasattr(codemonkeys.core, "AgentDefinition")
    assert hasattr(codemonkeys.core, "RunResult")
    assert hasattr(codemonkeys.core, "TokenUsage")


def test_core_importable_from_package() -> None:
    from codemonkeys.core import AgentDefinition, RunResult, TokenUsage

    assert AgentDefinition is not None
    assert RunResult is not None
    assert TokenUsage is not None


def test_runner_importable() -> None:
    from codemonkeys.core.runner import run_agent

    assert callable(run_agent)


def test_hooks_public_api() -> None:
    from codemonkeys.core.hooks import (
        build_check_hooks,
        build_permission_hooks,
        check_tool_allowed,
        merge_hooks,
    )

    assert callable(build_check_hooks)
    assert callable(build_permission_hooks)
    assert callable(check_tool_allowed)
    assert callable(merge_hooks)


def test_events_importable() -> None:
    from codemonkeys.core.events import (
        AgentCompleted,
        AgentError,
        AgentStarted,
        CheckResult,
        EventCollector,
        RateLimitHit,
        RawMessage,
        TextOutput,
        ThinkingOutput,
        TokenUpdate,
        ToolCall,
        ToolDenied,
        ToolResult,
    )

    assert AgentStarted is not None
    assert EventCollector is not None


def test_discovery_importable() -> None:
    from codemonkeys.core.discovery import batch, discover_files

    assert callable(batch)
    assert callable(discover_files)


def test_sandbox_importable() -> None:
    from codemonkeys.core.sandbox import is_restricted, restrict

    assert callable(is_restricted)
    assert callable(restrict)
