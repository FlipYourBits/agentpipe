"""Tests covering line 247 of codemonkeys/core/hooks.py.

Line 247 is the ``return {"decision": "block", ...}`` branch inside the
``UserPromptSubmit`` handler when the shell command exits with a non-zero
status code.
"""

from __future__ import annotations

import asyncio

from codemonkeys.core.hooks import build_check_hooks


def test_shell_hook_user_prompt_submit_failing_blocks() -> None:
    """When the command fails, UserPromptSubmit returns a block decision."""
    checks = {"UserPromptSubmit": [("*", "false")]}
    hooks = build_check_hooks(checks)
    hook_fn = hooks["UserPromptSubmit"][0].hooks[0]

    hook_input = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "",
        "cwd": "",
    }
    result = asyncio.run(hook_fn(hook_input, None, None))
    assert result["decision"] == "block"
    assert "reason" in result
