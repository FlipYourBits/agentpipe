from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from pydantic import BaseModel

from codemonkeys.core.types import (
    AgentDefinition,
    RunResult,
    TokenUsage,
    json_safe,
    make_log_dir,
)


class DummySchema(BaseModel):
    message: str


def test_agent_definition_is_frozen():
    agent = AgentDefinition(
        name="test",
        model="sonnet",
        system_prompt="You are a test agent.",
        tools=["Read", "Grep"],
    )
    assert agent.name == "test"
    assert agent.output_schema is None
    try:
        agent.name = "changed"  # type: ignore[misc]
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_agent_definition_with_schema():
    agent = AgentDefinition(
        name="reviewer",
        model="haiku",
        system_prompt="Review code.",
        tools=["Read"],
        output_schema=DummySchema,
    )
    assert agent.output_schema is DummySchema


def test_token_usage_defaults():
    usage = TokenUsage(input_tokens=100, output_tokens=50)
    assert usage.cache_read_tokens == 0
    assert usage.cache_creation_tokens == 0


def test_run_result_fields():
    usage = TokenUsage(input_tokens=1000, output_tokens=200)
    result = RunResult(
        output=None,
        text="hello",
        usage=usage,
        cost_usd=0.01,
        duration_ms=500,
    )
    assert result.error is None
    assert result.cost_usd == 0.01


# ---------------------------------------------------------------------------
# json_safe
# ---------------------------------------------------------------------------


def test_json_safe_none() -> None:
    assert json_safe(None) is None


def test_json_safe_string() -> None:
    assert json_safe("hello") == "hello"


def test_json_safe_int() -> None:
    assert json_safe(42) == 42


def test_json_safe_float() -> None:
    assert json_safe(3.14) == 3.14


def test_json_safe_bool() -> None:
    assert json_safe(True) is True
    assert json_safe(False) is False


def test_json_safe_dict() -> None:
    result = json_safe({"a": 1, "b": "two"})
    assert result == {"a": 1, "b": "two"}


def test_json_safe_dict_with_non_string_keys() -> None:
    result = json_safe({1: "one", 2: "two"})
    assert "1" in result
    assert "2" in result


def test_json_safe_list() -> None:
    result = json_safe([1, "two", 3.0])
    assert result == [1, "two", 3.0]


def test_json_safe_tuple() -> None:
    result = json_safe((1, 2, 3))
    assert result == [1, 2, 3]


def test_json_safe_nested() -> None:
    result = json_safe({"nums": [1, 2], "nested": {"x": None}})
    assert result == {"nums": [1, 2], "nested": {"x": None}}


def test_json_safe_type_class() -> None:
    class Foo:
        pass

    result = json_safe(Foo)
    assert result == "Foo"


def test_json_safe_pydantic_model() -> None:
    class MyModel(BaseModel):
        x: int = 5
        y: str = "hi"

    result = json_safe(MyModel())
    assert result == {"x": 5, "y": "hi"}


def test_json_safe_dataclass() -> None:
    @dataclasses.dataclass
    class Point:
        x: int
        y: int

    result = json_safe(Point(3, 4))
    assert result == {"x": 3, "y": 4}


def test_json_safe_object_with_dict() -> None:
    class Obj:
        def __init__(self) -> None:
            self.pub = "visible"
            self._priv = "hidden"

    result = json_safe(Obj())
    assert result == {"pub": "visible"}


def test_json_safe_unknown_object() -> None:
    # object() has no __dict__, no model_dump — falls to repr()
    result = json_safe(object())
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# make_log_dir
# ---------------------------------------------------------------------------


def test_make_log_dir_creates_timestamped_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_dir = make_log_dir("mytest")
    assert log_dir.exists()
    assert log_dir.is_dir()
    assert "mytest" in log_dir.name


def test_make_log_dir_without_label(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_dir = make_log_dir()
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_make_log_dir_under_codemonkeys_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_dir = make_log_dir("check")
    assert ".codemonkeys" in str(log_dir)
    assert "logs" in str(log_dir)


