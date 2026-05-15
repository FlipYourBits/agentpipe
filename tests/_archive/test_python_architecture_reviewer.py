"""Tests for codemonkeys/agents/python_architecture_reviewer.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from codemonkeys.agents.python_architecture_reviewer import (
    ArchitectureFinding,
    ArchitectureFindings,
    format_findings_markdown,
    make_python_architecture_reviewer,
)
from codemonkeys.core.types import AgentDefinition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_FILES = ["codemonkeys/agents/foo.py", "codemonkeys/core/bar.py"]
_FAKE_METADATA = "### `codemonkeys/agents/foo.py`\n  External imports: os"


def _make(files: list[str] = _FAKE_FILES, metadata: str = _FAKE_METADATA) -> AgentDefinition:
    """Call make_python_architecture_reviewer with mocked side-effectful helpers."""
    with (
        patch(
            "codemonkeys.agents.python_architecture_reviewer.discover_files",
            return_value=files,
        ),
        patch(
            "codemonkeys.agents.python_architecture_reviewer.analyze_files",
            return_value=[],
        ),
        patch(
            "codemonkeys.agents.python_architecture_reviewer.format_analysis",
            return_value=metadata,
        ),
    ):
        return make_python_architecture_reviewer()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_make_python_architecture_reviewer_returns_agent_definition() -> None:
    result = _make()
    assert isinstance(result, AgentDefinition)


def test_make_python_architecture_reviewer_name_encodes_file_count() -> None:
    result = _make(files=_FAKE_FILES)
    assert result.name == f"python_architecture_reviewer:{len(_FAKE_FILES)}_files"


def test_make_python_architecture_reviewer_name_with_zero_files() -> None:
    result = _make(files=[])
    assert result.name == "python_architecture_reviewer:0_files"


def test_make_python_architecture_reviewer_name_with_single_file() -> None:
    result = _make(files=["only.py"])
    assert result.name == "python_architecture_reviewer:1_files"


def test_make_python_architecture_reviewer_model_is_opus() -> None:
    result = _make()
    assert result.model == "opus"


def test_make_python_architecture_reviewer_tools_contains_read() -> None:
    result = _make()
    assert result.tools == ["Read", "Grep"]


def test_make_python_architecture_reviewer_output_schema_is_architecture_findings() -> None:
    result = _make()
    assert result.output_schema is ArchitectureFindings


def test_make_python_architecture_reviewer_system_prompt_contains_file_list() -> None:
    files = ["codemonkeys/agents/foo.py", "codemonkeys/core/bar.py"]
    result = _make(files=files)
    for f in files:
        assert f"`{f}`" in result.system_prompt


def test_make_python_architecture_reviewer_system_prompt_contains_metadata() -> None:
    metadata = "### `some/path.py`\n  External imports: pathlib"
    result = _make(metadata=metadata)
    assert metadata in result.system_prompt


def test_make_python_architecture_reviewer_discover_files_called_with_py_glob() -> None:
    with (
        patch(
            "codemonkeys.agents.python_architecture_reviewer.discover_files",
            return_value=[],
        ) as mock_discover,
        patch(
            "codemonkeys.agents.python_architecture_reviewer.analyze_files",
            return_value=[],
        ),
        patch(
            "codemonkeys.agents.python_architecture_reviewer.format_analysis",
            return_value="",
        ),
    ):
        make_python_architecture_reviewer()
        mock_discover.assert_called_once_with("**/*.py")


def test_make_python_architecture_reviewer_analyze_files_receives_discovered_files() -> None:
    files = ["a.py", "b.py"]
    with (
        patch(
            "codemonkeys.agents.python_architecture_reviewer.discover_files",
            return_value=files,
        ),
        patch(
            "codemonkeys.agents.python_architecture_reviewer.analyze_files",
            return_value=[],
        ) as mock_analyze,
        patch(
            "codemonkeys.agents.python_architecture_reviewer.format_analysis",
            return_value="",
        ),
    ):
        make_python_architecture_reviewer()
        mock_analyze.assert_called_once_with(files)


def test_make_python_architecture_reviewer_format_analysis_output_used() -> None:
    sentinel = "UNIQUE_SENTINEL_STRING_XYZ"
    result = _make(metadata=sentinel)
    assert sentinel in result.system_prompt


def test_make_python_architecture_reviewer_file_list_markdown_format() -> None:
    files = ["x/y.py"]
    result = _make(files=files)
    # Each file must appear as a markdown list item with backtick-quoted path
    assert "- `x/y.py`" in result.system_prompt


def test_make_python_architecture_reviewer_empty_file_list_still_returns_definition() -> None:
    result = _make(files=[], metadata="")
    assert isinstance(result, AgentDefinition)
    assert result.name == "python_architecture_reviewer:0_files"


# ---------------------------------------------------------------------------
# format_findings_markdown
# ---------------------------------------------------------------------------


def _finding(**overrides) -> ArchitectureFinding:
    defaults = {
        "files": ["a.py", "b.py"],
        "severity": "medium",
        "category": "design",
        "subcategory": "dependency_coupling",
        "title": "Circular import",
        "description": "a.py and b.py import each other.",
        "suggestion": "Extract shared code to a third module.",
    }
    return ArchitectureFinding(**(defaults | overrides))


def test_format_findings_markdown_empty() -> None:
    result = ArchitectureFindings(files_reviewed=["a.py"], findings=[])
    md = format_findings_markdown(result)
    assert "No cross-file design issues found." in md


def test_format_findings_markdown_has_title() -> None:
    result = ArchitectureFindings(files_reviewed=["a.py"], findings=[_finding()])
    md = format_findings_markdown(result)
    assert "# Architecture Review Findings" in md


def test_format_findings_markdown_numbered() -> None:
    result = ArchitectureFindings(
        files_reviewed=["a.py"],
        findings=[_finding(title="First"), _finding(title="Second")],
    )
    md = format_findings_markdown(result)
    assert "## 1. [MEDIUM] First" in md
    assert "## 2. [MEDIUM] Second" in md


def test_format_findings_markdown_includes_fields() -> None:
    result = ArchitectureFindings(files_reviewed=["a.py"], findings=[_finding()])
    md = format_findings_markdown(result)
    assert "`a.py`" in md
    assert "`b.py`" in md
    assert "dependency_coupling" in md
    assert "a.py and b.py import each other." in md
    assert "Extract shared code to a third module." in md


def test_format_findings_markdown_no_suggestion() -> None:
    result = ArchitectureFindings(
        files_reviewed=["a.py"],
        findings=[_finding(suggestion=None)],
    )
    md = format_findings_markdown(result)
    assert "**Suggestion:**" not in md
