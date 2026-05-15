"""Additional tests to cover remaining lines in codemonkeys.display.formatting."""

from __future__ import annotations

from codemonkeys.display.formatting import system_message_label


# ---------------------------------------------------------------------------
# system_message_label — hook_response branch (lines 131-133)
# ---------------------------------------------------------------------------


def test_system_message_label_hook_response():
    data = {"subtype": "hook_response", "data": {"hook_name": "pre_tool", "outcome": "approved"}}
    assert system_message_label(data) == "hook response: pre_tool (approved)"


def test_system_message_label_hook_response_missing_keys():
    data = {"subtype": "hook_response", "data": {}}
    assert system_message_label(data) == "hook response: ? (?)"


def test_system_message_label_hook_response_no_data_key():
    # "data" key absent entirely — inner defaults to {} so both values fall back to "?"
    data = {"subtype": "hook_response"}
    assert system_message_label(data) == "hook response: ? (?)"


# ---------------------------------------------------------------------------
# system_message_label — final fallback (line 126)
# ---------------------------------------------------------------------------


def test_system_message_label_none_subtype():
    # Explicit None is falsy — returns plain "system" without a colon suffix
    data = {"subtype": None}
    assert system_message_label(data) == "system"
