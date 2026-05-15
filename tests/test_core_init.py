"""Characterization tests for codemonkeys/core/__init__.py."""

from __future__ import annotations

import codemonkeys.core as core_module
from codemonkeys.core import AgentDefinition, RunResult, TokenUsage


def test_core_exports_agent_definition() -> None:
    assert AgentDefinition is not None


def test_core_exports_run_result() -> None:
    assert RunResult is not None


def test_core_exports_token_usage() -> None:
    assert TokenUsage is not None


def test_core_all_contains_expected_names() -> None:
    assert "AgentDefinition" in core_module.__all__
    assert "RunResult" in core_module.__all__
    assert "TokenUsage" in core_module.__all__


def test_core_all_length() -> None:
    assert len(core_module.__all__) == 3


def test_core_exports_are_correct_types() -> None:
    from codemonkeys.core.types import (
        AgentDefinition as AD,
        RunResult as RR,
        TokenUsage as TU,
    )

    assert AgentDefinition is AD
    assert RunResult is RR
    assert TokenUsage is TU
