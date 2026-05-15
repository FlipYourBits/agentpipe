from codemonkeys.prompts.refactoring import REFACTOR_INSTRUCTIONS


def test_refactor_instructions_contains_expected_keys() -> None:
    expected = {"circular_deps", "layering", "god_modules", "extract_shared", "dead_code", "naming"}
    assert set(REFACTOR_INSTRUCTIONS.keys()) == expected


def test_each_instruction_is_nonempty_string() -> None:
    for key, value in REFACTOR_INSTRUCTIONS.items():
        assert isinstance(value, str), f"{key} is not a string"
        assert len(value) > 0, f"{key} is empty"
