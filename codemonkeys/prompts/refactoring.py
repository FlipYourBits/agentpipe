"""Refactoring instructions — strategies for each structural refactor type."""

from __future__ import annotations

REFACTOR_INSTRUCTIONS: dict[str, str] = {
    "circular_deps": """\
Break the circular dependency described below. Common strategies:
- Extract shared types/interfaces into a third module both can import.
- Invert the dependency direction using dependency injection.
- Merge the modules if they are conceptually one unit.
- Use late imports (inside functions) only as a last resort.""",
    "layering": """\
Fix the layer violation described below. The import crosses a boundary
that should be respected. Move the shared code to the appropriate layer,
or restructure so the lower layer doesn't depend on the higher one.""",
    "god_modules": """\
Split the oversized module into focused, single-responsibility modules.
- Identify cohesive groups of functions/classes that work together.
- Extract each group into its own module.
- Update imports across the codebase to point to the new locations.
- The original module can re-export for backwards compatibility if needed.""",
    "extract_shared": """\
Extract duplicated code into a shared module.
- Identify the common pattern across the duplicate sites.
- Create a single implementation in an appropriate shared location.
- Replace all duplicate sites with calls to the shared code.
- Ensure the shared interface is clean and well-named.""",
    "dead_code": """\
Remove the dead code identified below. Verify it is truly unreachable:
- Check for dynamic references (getattr, importlib, string-based dispatch).
- Check for use in tests, scripts, or CLI entry points.
- If truly dead, delete it cleanly with no stubs or comments.""",
    "naming": """\
Rename the inconsistent identifiers below to match the codebase convention.
- Update ALL references across the codebase (imports, calls, strings).
- Use your editor tools to find all occurrences before renaming.
- Verify no references are missed after renaming.""",
}
