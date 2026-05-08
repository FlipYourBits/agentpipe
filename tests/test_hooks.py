import asyncio

from codemonkeys.core.hooks import (
    build_check_hooks,
    build_tool_hooks,
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


# --- build_tool_hooks ---


def test_build_tool_hooks_returns_none_when_no_patterns():
    hooks = build_tool_hooks(["Read", "Grep"])
    assert hooks is None


def test_build_tool_hooks_returns_hooks_for_bash_patterns():
    hooks = build_tool_hooks(["Read", "Bash(pytest*)"])
    assert hooks is not None
    assert "PreToolUse" in hooks
    matchers = hooks["PreToolUse"]
    assert any(m.matcher == "Bash" for m in matchers)


def test_build_tool_hooks_returns_hooks_for_read_patterns():
    hooks = build_tool_hooks(["Read(src/*)", "Grep"])
    assert hooks is not None
    assert "PreToolUse" in hooks
    matchers = hooks["PreToolUse"]
    assert any(m.matcher == "Read" for m in matchers)


def test_build_tool_hooks_multiple_tools_with_patterns():
    hooks = build_tool_hooks(["Read(src/*)", "Bash(git*)", "Edit(src/*)"])
    assert hooks is not None
    matchers = hooks["PreToolUse"]
    matcher_names = {m.matcher for m in matchers}
    assert matcher_names == {"Read", "Bash", "Edit"}


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
    a = {"PreToolUse": [build_tool_hooks(["Bash(git*)"])["PreToolUse"][0]]}
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
