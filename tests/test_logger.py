import json
import tempfile
import time
from pathlib import Path

from codemonkeys.core.events import AgentStarted, ToolCall
from codemonkeys.core.types import AgentDefinition
from codemonkeys.display.logger import FileLogger, load_run_meta, save_run_meta


def test_file_logger_writes_jsonl():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name

    logger = FileLogger(path)
    logger.handle(AgentStarted(agent_name="test", timestamp=1000.0, model="sonnet"))
    logger.handle(
        ToolCall(
            agent_name="test",
            timestamp=1001.0,
            tool_name="Read",
            tool_input={"file_path": "/foo.py"},
        )
    )
    logger.close()

    lines = Path(path).read_text().strip().split("\n")
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["agent_name"] == "test"
    assert first["model"] == "sonnet"

    second = json.loads(lines[1])
    assert second["tool_name"] == "Read"


def test_file_logger_as_event_handler():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name

    logger = FileLogger(path)
    event = AgentStarted(agent_name="x", timestamp=time.time(), model="haiku")
    logger.handle(event)
    logger.close()

    lines = Path(path).read_text().strip().split("\n")
    assert len(lines) == 1


def test_save_run_meta_writes_json(tmp_path: Path) -> None:
    agent = AgentDefinition(
        name="test_agent",
        model="sonnet",
        system_prompt="You are a test agent.",
        tools=["Read(foo.py)", "Edit(foo.py)"],
    )
    save_run_meta(tmp_path, "run_01", agent, "Do the thing.")
    path = tmp_path / "run_01_meta.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["agent_name"] == "test_agent"
    assert data["model"] == "sonnet"
    assert data["system_prompt"] == "You are a test agent."
    assert data["tools"] == ["Read(foo.py)", "Edit(foo.py)"]
    assert data["prompt"] == "Do the thing."


def test_load_run_meta_roundtrips(tmp_path: Path) -> None:
    agent = AgentDefinition(
        name="roundtrip",
        model="opus",
        system_prompt="prompt text",
        tools=["Read"],
    )
    save_run_meta(tmp_path, "rt", agent, "the prompt")
    loaded = load_run_meta(tmp_path / "rt_meta.json")
    assert loaded["agent_name"] == "roundtrip"
    assert loaded["prompt"] == "the prompt"
