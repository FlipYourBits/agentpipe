"""Hook builders — tool permission enforcement and automated checks.

## Tool pattern restrictions (PreToolUse)

Supports pattern-restricted tools via the syntax ``Tool(glob_pattern)``.
The pattern is matched against a tool-specific input field:

    Bash(git log*)        — matches the ``command`` field
    Read(codemonkeys/*)   — matches the ``file_path`` field
    Edit(codemonkeys/*)   — matches the ``file_path`` field
    Write(codemonkeys/*)  — matches the ``file_path`` field
    Glob(src/*)           — matches the ``pattern`` field
    Grep(codemonkeys/*)   — matches the ``path`` field
    WebFetch(https://docs.example.com/*) — matches the ``url`` field
    WebSearch(python*)    — matches the ``query`` field

A bare tool name (e.g. ``Read``) allows all inputs for that tool.

## Automated checks (PostToolUse / Stop)

Shell commands declared on ``AgentDefinition.hooks`` run automatically
at the specified hook event. Commands can interpolate ``{field}``
placeholders from the tool's input (e.g. ``{file_path}``).

PostToolUse checks inject their output via ``additionalContext``.
Stop checks block the agent from finishing if the command fails.
"""

from __future__ import annotations

import asyncio
import fnmatch
import re
from typing import Any

from claude_agent_sdk import HookCallback, HookInput, HookMatcher
from claude_agent_sdk.types import HookEvent, SyncHookJSONOutput

from codemonkeys.core.types import AgentHooks

_TOOL_PATTERN_RE = re.compile(r"^(\w+)\((.+)\)$")

_TOOL_INPUT_FIELDS: dict[str, str] = {
    "Bash": "command",
    "Read": "file_path",
    "Write": "file_path",
    "Edit": "file_path",
    "Glob": "pattern",
    "Grep": "path",
    "WebFetch": "url",
    "WebSearch": "query",
}


def _parse_tool_patterns(tools: list[str]) -> dict[str, list[str]]:
    """Extract ``{tool_name: [glob_patterns]}`` from Tool(pattern) entries."""
    result: dict[str, list[str]] = {}
    for spec in tools:
        m = _TOOL_PATTERN_RE.match(spec)
        if m:
            tool_name, pattern = m.group(1), m.group(2)
            result.setdefault(tool_name, []).append(pattern)
    return result


def _has_bare_tool(tool_name: str, tools: list[str]) -> bool:
    """Check if a bare tool name (without pattern) is in the allowlist."""
    return tool_name in tools and not any(
        _TOOL_PATTERN_RE.match(t) and _TOOL_PATTERN_RE.match(t).group(1) == tool_name  # type: ignore[union-attr]
        for t in tools
        if t == tool_name
    )


def _get_match_value(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Extract the value to match against from a tool's input dict."""
    field = _TOOL_INPUT_FIELDS.get(tool_name)
    if field is None:
        return ""
    return str(tool_input.get(field, "")).strip()


def check_tool_allowed(
    tool_name: str, tool_input: dict[str, Any], allowed_tools: list[str]
) -> bool:
    """Check if a tool call is permitted by the allowlist."""
    if tool_name in allowed_tools:
        return True

    all_patterns = _parse_tool_patterns(allowed_tools)
    patterns = all_patterns.get(tool_name)
    if not patterns:
        return False

    value = _get_match_value(tool_name, tool_input)
    if not value:
        return False
    return any(fnmatch.fnmatch(value, p) for p in patterns)


OnDenyCallback = Any  # (tool_name: str, detail: str) -> None


def _make_hook_fn(
    tool_name: str,
    patterns: list[str],
    on_deny: OnDenyCallback | None,
) -> HookCallback:
    """Build a PreToolUse hook that enforces patterns for a single tool."""
    field = _TOOL_INPUT_FIELDS.get(tool_name, "command")

    async def _enforce(
        hook_input: HookInput,
        _tool_use_id: str | None,
        _context: Any,
    ) -> SyncHookJSONOutput:
        value = str(hook_input["tool_input"].get(field, "")).strip()  # type: ignore[typeddict-item]
        for pattern in patterns:
            if fnmatch.fnmatch(value, pattern):
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                    }
                }
        if on_deny:
            on_deny(tool_name, value)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{tool_name} input not allowed. "
                    f"Permitted patterns for {field}: {patterns}"
                ),
            }
        }

    return _enforce  # type: ignore[return-value]


def build_permission_hooks(
    allowed_tools: list[str],
    on_deny: OnDenyCallback | None = None,
) -> dict[HookEvent, list[HookMatcher]]:
    """Build PreToolUse hooks that enforce pattern-restricted tools."""
    all_patterns = _parse_tool_patterns(allowed_tools)
    if not all_patterns:
        return {}

    matchers: list[HookMatcher] = []
    for tool_name, patterns in all_patterns.items():
        hook_fn = _make_hook_fn(tool_name, patterns, on_deny)
        matchers.append(HookMatcher(matcher=tool_name, hooks=[hook_fn]))

    return {"PreToolUse": matchers}


# Keep the old name as an alias for backwards compatibility
def build_tool_hooks(
    allowed_tools: list[str],
    on_deny: OnDenyCallback | None = None,
) -> dict[HookEvent, list[HookMatcher]] | None:
    result = build_permission_hooks(allowed_tools, on_deny)
    return result or None


# ---------------------------------------------------------------------------
# Automated checks — shell commands that run at PostToolUse / Stop
# ---------------------------------------------------------------------------

_MAX_CHECK_OUTPUT = 4000

OnCheckCallback = Any  # (hook_event: str, command: str, passed: bool, output: str) -> None


def _shell_hook(
    command_template: str,
    event: str,
    agent_name: str,
    on_check: OnCheckCallback | None,
) -> HookCallback:
    """Turn a shell command template into an SDK hook callback.

    Placeholders like ``{file_path}`` are interpolated from the hook's
    ``tool_input`` dict.  For Stop hooks (no tool_input), the command
    runs as-is.
    """

    async def _run(
        hook_input: HookInput,
        _tool_use_id: str | None,
        _context: Any,
    ) -> SyncHookJSONOutput:
        tool_input: dict[str, Any] = hook_input.get("tool_input", {})  # type: ignore[typeddict-item]
        try:
            command = command_template.format_map(tool_input)
        except KeyError:
            command = command_template

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        raw_output, _ = await proc.communicate()
        output = raw_output.decode(errors="replace").strip()
        if len(output) > _MAX_CHECK_OUTPUT:
            output = output[:_MAX_CHECK_OUTPUT] + "\n... (truncated)"

        passed = proc.returncode == 0

        if on_check:
            on_check(event, command, passed, output)

        label = "PASS" if passed else "FAIL"
        message = f"[check {label}] `{command}`\n{output}" if output else f"[check {label}] `{command}`"

        if event == "PostToolUse":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                }
            }

        if event == "SubagentStart":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": message,
                }
            }

        # Stop hook — block the agent from finishing if the check failed
        if not passed:
            return {
                "decision": "block",
                "reason": message,
            }
        return {}

    return _run  # type: ignore[return-value]


def build_check_hooks(
    checks: AgentHooks,
    agent_name: str = "",
    on_check: OnCheckCallback | None = None,
) -> dict[HookEvent, list[HookMatcher]]:
    """Build hooks from an AgentDefinition's ``checks`` dict.

    Each entry maps an SDK hook event name (e.g. ``"PostToolUse"``,
    ``"Stop"``) to a list of ``(matcher, shell_command)`` pairs.
    """
    result: dict[HookEvent, list[HookMatcher]] = {}
    for event_name, entries in checks.items():
        matchers: list[HookMatcher] = []
        for matcher, command in entries:
            hook_fn = _shell_hook(command, event_name, agent_name, on_check)
            matchers.append(HookMatcher(matcher=matcher, hooks=[hook_fn]))
        if matchers:
            result[event_name] = matchers  # type: ignore[assignment]
    return result


def merge_hooks(
    *hook_dicts: dict[HookEvent, list[HookMatcher]] | None,
) -> dict[HookEvent, list[HookMatcher]] | None:
    """Merge multiple hook dicts into one, concatenating matchers per event."""
    merged: dict[HookEvent, list[HookMatcher]] = {}
    for hooks in hook_dicts:
        if not hooks:
            continue
        for event, matchers in hooks.items():
            merged.setdefault(event, []).extend(matchers)
    return merged or None
