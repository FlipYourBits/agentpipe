from __future__ import annotations

import asyncio

from codemonkeys.core.hooks import (
    _matches_pattern,
    build_check_hooks,
    build_permission_hooks,
    check_tool_allowed,
    merge_hooks,
)


# --- check_tool_allowed: bare tool names ---


def test_bare_tool_allowed():
    allowed = ["Read", "Grep", "Bash(pytest*)"]
    assert check_tool_allowed("Read", {}, allowed) is True
    assert check_tool_allowed("Grep", {}, allowed) is True


def test_bare_tool_not_in_list():
    allowed = ["Read", "Grep", "Bash(pytest*)"]
    assert check_tool_allowed("Edit", {}, allowed) is False
    assert check_tool_allowed("Write", {}, allowed) is False


def test_empty_allowlist():
    assert check_tool_allowed("Read", {}, []) is False
    assert check_tool_allowed("Bash", {"command": "ls"}, []) is False


# --- check_tool_allowed: Bash patterns ---


def test_bash_patterns_match():
    allowed = ["Read", "Bash(pytest*)", "Bash(ruff*)"]
    assert check_tool_allowed("Bash", {"command": "pytest tests/ -v"}, allowed) is True
    assert check_tool_allowed("Bash", {"command": "ruff check ."}, allowed) is True


def test_bash_patterns_deny():
    allowed = ["Read", "Bash(pytest*)", "Bash(ruff*)"]
    assert check_tool_allowed("Bash", {"command": "rm -rf /"}, allowed) is False
    assert check_tool_allowed("Bash", {"command": ""}, allowed) is False


def test_bare_bash_allows_anything():
    allowed = ["Read", "Bash"]
    assert check_tool_allowed("Bash", {"command": "anything"}, allowed) is True


# --- check_tool_allowed: Read patterns ---


def test_read_pattern_match():
    allowed = ["Read(codemonkeys/*)"]
    assert (
        check_tool_allowed("Read", {"file_path": "codemonkeys/agents/fixer.py"}, allowed)
        is True
    )


def test_read_pattern_deny():
    allowed = ["Read(codemonkeys/*)"]
    assert check_tool_allowed("Read", {"file_path": "/etc/passwd"}, allowed) is False


def test_bare_read_allows_any_path():
    allowed = ["Read"]
    assert check_tool_allowed("Read", {"file_path": "/etc/passwd"}, allowed) is True


# --- check_tool_allowed: Edit patterns ---


def test_edit_pattern_match():
    allowed = ["Edit(src/*)"]
    assert check_tool_allowed("Edit", {"file_path": "src/main.py"}, allowed) is True
    assert check_tool_allowed("Edit", {"file_path": "tests/test.py"}, allowed) is False


# --- check_tool_allowed: Write patterns ---


def test_write_pattern_match():
    allowed = ["Write(tests/*)"]
    assert check_tool_allowed("Write", {"file_path": "tests/test_new.py"}, allowed) is True
    assert check_tool_allowed("Write", {"file_path": "src/main.py"}, allowed) is False


# --- check_tool_allowed: WebFetch patterns ---


def test_webfetch_pattern_match():
    allowed = ["WebFetch(https://docs.example.com/*)"]
    assert (
        check_tool_allowed(
            "WebFetch", {"url": "https://docs.example.com/api/v1"}, allowed
        )
        is True
    )
    assert (
        check_tool_allowed("WebFetch", {"url": "https://evil.com/steal"}, allowed)
        is False
    )


# --- check_tool_allowed: Grep patterns ---


def test_grep_pattern_match():
    allowed = ["Grep(codemonkeys/*)"]
    assert check_tool_allowed("Grep", {"path": "codemonkeys/core"}, allowed) is True
    assert check_tool_allowed("Grep", {"path": "/etc"}, allowed) is False


# --- check_tool_allowed: multiple patterns for same tool ---


def test_multiple_patterns_for_same_tool():
    allowed = ["Read(src/*)", "Read(tests/*)"]
    assert check_tool_allowed("Read", {"file_path": "src/main.py"}, allowed) is True
    assert check_tool_allowed("Read", {"file_path": "tests/test.py"}, allowed) is True
    assert check_tool_allowed("Read", {"file_path": "docs/readme.md"}, allowed) is False


# --- check_tool_allowed: mixed bare and patterned tools ---


def test_mixed_tools():
    allowed = ["Grep", "Read(codemonkeys/*)", "Bash(git log*)"]
    assert check_tool_allowed("Grep", {"path": "anywhere"}, allowed) is True
    assert (
        check_tool_allowed("Read", {"file_path": "codemonkeys/core/types.py"}, allowed)
        is True
    )
    assert check_tool_allowed("Read", {"file_path": "/etc/shadow"}, allowed) is False
    assert check_tool_allowed("Bash", {"command": "git log --oneline"}, allowed) is True
    assert check_tool_allowed("Bash", {"command": "rm -rf /"}, allowed) is False


# --- check_tool_allowed: unknown tool with pattern ---


def test_unknown_tool_with_pattern():
    allowed = ["CustomTool(abc*)"]
    assert check_tool_allowed("CustomTool", {"whatever": "abcdef"}, allowed) is False


# --- build_check_hooks ---


def test_build_check_hooks_post_tool_use():
    checks = {
        "PostToolUse": [("Edit", "echo lint {file_path}")],
    }
    hooks = build_check_hooks(checks)
    assert "PostToolUse" in hooks
    matchers = hooks["PostToolUse"]
    assert len(matchers) == 1
    assert matchers[0].matcher == "Edit"


def test_build_check_hooks_stop():
    checks = {
        "Stop": [(None, "echo tests")],
    }
    hooks = build_check_hooks(checks)
    assert "Stop" in hooks
    assert hooks["Stop"][0].matcher is None


def test_build_check_hooks_empty():
    assert build_check_hooks({}) == {}


def test_build_check_hooks_multiple_events():
    checks = {
        "PostToolUse": [("Edit", "echo lint"), ("Write", "echo format")],
        "Stop": [(None, "echo test")],
    }
    hooks = build_check_hooks(checks)
    assert len(hooks["PostToolUse"]) == 2
    assert len(hooks["Stop"]) == 1


# --- shell hook behavior ---


def test_shell_hook_post_tool_use_passing():
    checks = {"PostToolUse": [("Edit", "echo ok")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/main.py"},
        "tool_response": "",
        "tool_use_id": "123",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "123", None))
    specific = result.get("hookSpecificOutput", {})
    assert specific.get("hookEventName") == "PostToolUse"
    assert "ok" in specific.get("additionalContext", "")


def test_shell_hook_post_tool_use_interpolates_file_path():
    checks = {"PostToolUse": [("Edit", "echo {file_path}")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/main.py"},
        "tool_response": "",
        "tool_use_id": "123",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "123", None))
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "src/main.py" in context


def test_shell_hook_stop_passing():
    checks = {"Stop": [(None, "true")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["Stop"][0].hooks[0]

    hook_input = {
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
    }
    result = asyncio.run(hook_fn(hook_input, None, None))
    assert result.get("decision") != "block"


def test_shell_hook_stop_failing_blocks():
    checks = {"Stop": [(None, "false")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["Stop"][0].hooks[0]

    hook_input = {
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
    }
    result = asyncio.run(hook_fn(hook_input, None, None))
    assert result["decision"] == "block"


# --- merge_hooks ---


def test_merge_hooks_combines_events():
    a = {"PreToolUse": [build_permission_hooks(["Bash(git*)"])["PreToolUse"][0]]}
    b = {"PostToolUse": [build_check_hooks({"PostToolUse": [("Edit", "echo ok")]})["PostToolUse"][0]]}
    merged = merge_hooks(a, b)
    assert merged is not None
    assert "PreToolUse" in merged
    assert "PostToolUse" in merged


def test_merge_hooks_concatenates_same_event():
    a = {"PostToolUse": [build_check_hooks({"PostToolUse": [("Edit", "echo a")]})["PostToolUse"][0]]}
    b = {"PostToolUse": [build_check_hooks({"PostToolUse": [("Write", "echo b")]})["PostToolUse"][0]]}
    merged = merge_hooks(a, b)
    assert merged is not None
    assert len(merged["PostToolUse"]) == 2


def test_merge_hooks_all_none():
    assert merge_hooks(None, None) is None


# --- _matches_pattern — edge cases ---


def test_matches_pattern_direct_fnmatch() -> None:
    assert _matches_pattern("pytest tests/", "pytest*", "command") is True


def test_matches_pattern_no_match() -> None:
    assert _matches_pattern("rm -rf /", "pytest*", "command") is False


def test_matches_pattern_path_field_relative(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    abs_path = str(tmp_path / "src" / "main.py")
    assert _matches_pattern(abs_path, "src/*", "file_path") is True


def test_matches_pattern_value_error_on_different_drive(monkeypatch) -> None:
    # On Linux, os.path.relpath between paths on different drives (simulated)
    # can raise ValueError. We simulate that by patching os.path.relpath.
    import os
    from unittest.mock import patch

    with patch("os.path.relpath", side_effect=ValueError("different drive")):
        result = _matches_pattern("/some/abs/path", "src/*", "file_path")
    assert result is False


# --- build_permission_hooks ---


def test_build_permission_hooks_returns_empty_for_bare_tools() -> None:
    result = build_permission_hooks(["Read", "Grep"])
    assert result == {}


def test_build_permission_hooks_has_pre_tool_use_key() -> None:
    result = build_permission_hooks(["Bash(pytest*)"])
    assert "PreToolUse" in result


def test_build_permission_hooks_allow_branch():
    """The hook allows a call whose input matches the pattern."""
    hooks = build_permission_hooks(["Bash(pytest*)"])
    hook_fn = hooks["PreToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/ -v"},
        "tool_use_id": "id-1",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "id-1", None))
    assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_build_permission_hooks_deny_branch():
    """The hook denies a call whose input doesn't match the pattern."""
    hooks = build_permission_hooks(["Bash(pytest*)"])
    hook_fn = hooks["PreToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"},
        "tool_use_id": "id-2",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "id-2", None))
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_build_permission_hooks_on_deny_callback_called():
    denied: list[tuple[str, str]] = []

    def on_deny(tool_name: str, command: str) -> None:
        denied.append((tool_name, command))

    hooks = build_permission_hooks(["Bash(git*)"], on_deny=on_deny)
    hook_fn = hooks["PreToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"},
        "tool_use_id": "id-3",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    asyncio.run(hook_fn(hook_input, "id-3", None))
    assert len(denied) == 1
    assert denied[0] == ("Bash", "rm -rf /")


def test_build_permission_hooks_on_deny_not_called_on_allow():
    denied: list[str] = []
    hooks = build_permission_hooks(["Bash(git*)"], on_deny=lambda t, c: denied.append(c))
    hook_fn = hooks["PreToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git log --oneline"},
        "tool_use_id": "id-4",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    asyncio.run(hook_fn(hook_input, "id-4", None))
    assert denied == []


# --- build_check_hooks — on_check callback ---


def test_build_check_hooks_on_check_called():
    received: list[tuple[str, str, bool]] = []

    def on_check(event: str, command: str, passed: bool, output: str) -> None:
        received.append((event, command, passed))

    checks = {"PostToolUse": [("Edit", "echo check_ok")]}
    hooks = build_check_hooks(checks, on_check=on_check)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/main.py"},
        "tool_response": "",
        "tool_use_id": "x",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    asyncio.run(hook_fn(hook_input, "x", None))
    assert len(received) == 1
    event, command, passed = received[0]
    assert event == "PostToolUse"
    assert passed is True


# --- shell hook: UserPromptSubmit event ---


def test_shell_hook_user_prompt_submit_returns_additional_context():
    checks = {"UserPromptSubmit": [("*", "echo prompt_ok")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["UserPromptSubmit"][0].hooks[0]

    hook_input = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "",
        "cwd": "",
    }
    result = asyncio.run(hook_fn(hook_input, None, None))
    specific = result.get("hookSpecificOutput", {})
    assert specific.get("hookEventName") == "UserPromptSubmit"
    assert "prompt_ok" in specific.get("additionalContext", "")


# --- shell hook: truncation of long output ---


def test_shell_hook_truncates_long_output():
    # Command that produces more than 4000 chars of output
    checks = {"PostToolUse": [("Edit", "python3 -c \"print('x' * 5000)\"")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "f.py"},
        "tool_response": "",
        "tool_use_id": "t",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "t", None))
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "truncated" in context


# --- shell hook: command with no output ---


def test_shell_hook_no_output_omits_output_from_message():
    checks = {"PostToolUse": [("Edit", "true")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "x.py"},
        "tool_response": "",
        "tool_use_id": "u",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    result = asyncio.run(hook_fn(hook_input, "u", None))
    # When there's no output, the message should not have a trailing newline+output
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "PASS" in context


# --- shell hook: missing placeholder key just uses template as-is ---


def test_shell_hook_missing_placeholder_uses_literal_command():
    checks = {"PostToolUse": [("Edit", "echo {nonexistent_field}")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["PostToolUse"][0].hooks[0]

    hook_input = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "x.py"},
        "tool_response": "",
        "tool_use_id": "v",
        "session_id": "",
        "transcript_path": "",
        "cwd": "",
        "agent_id": "",
        "agent_type": "",
    }
    # Should not raise; the template is used literally
    result = asyncio.run(hook_fn(hook_input, "v", None))
    assert "hookSpecificOutput" in result


# --- check_tool_allowed: WebSearch and Glob patterns ---


def test_websearch_pattern_match():
    allowed = ["WebSearch(python*)"]
    assert check_tool_allowed("WebSearch", {"query": "python typing"}, allowed) is True
    assert check_tool_allowed("WebSearch", {"query": "java generics"}, allowed) is False


def test_glob_pattern_match():
    allowed = ["Glob(src/*)"]
    assert check_tool_allowed("Glob", {"pattern": "src/**/*.py"}, allowed) is True
    assert check_tool_allowed("Glob", {"pattern": "tests/**"}, allowed) is False


# --- check_tool_allowed: absolute paths matched against relative patterns ---


def test_absolute_path_matches_relative_pattern(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    allowed = ["Read", "Edit(tests/*)", "Write(tests/*)"]
    abs_test = str(tmp_path / "tests" / "test_foo.py")
    abs_src = str(tmp_path / "src" / "main.py")
    assert check_tool_allowed("Edit", {"file_path": abs_test}, allowed) is True
    assert check_tool_allowed("Write", {"file_path": abs_test}, allowed) is True
    assert check_tool_allowed("Edit", {"file_path": abs_src}, allowed) is False
    assert check_tool_allowed("Write", {"file_path": abs_src}, allowed) is False
