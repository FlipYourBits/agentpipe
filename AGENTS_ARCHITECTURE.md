# Agents Architecture

## Agents

### 1. `python_reviewer`
- **Language:** Python-specific
- **What it does:** Per-file code review for quality, security, resilience, and test quality. Uses different checklists depending on whether the file is a test or source file.
- **Input:** A single `.py` file path. Called once per file.
- **Repo scope:** Runs on individual Python files — the caller decides which files to feed it. It reviews one file at a time.
- **Tools:** Read, Grep (read-only)

### 2. `architecture_reviewer`
- **Language:** Python-leaning (uses AST analysis), but the review concepts are language-agnostic
- **What it does:** Cross-file design review — import graph analysis, dependency direction, coupling, cycles, interface consistency, duplicated responsibilities. Receives per-file summaries from `python_reviewer` and structural metadata from `codemonkeys.core.analysis` (AST-based).
- **Input:** A list of file paths + per-file summaries from prior reviewers. Gets AST metadata injected via a `SubagentStart` hook.
- **Repo scope:** Runs across a batch of files (the full set being reviewed). Prefers not to read files directly — works from metadata and summaries.
- **Tools:** Read only (read-only)

### 3. `docs_reviewer`
- **Language:** Language-agnostic
- **What it does:** Verifies `README.md`, `CHANGELOG.md`, and `CLAUDE.md` against the actual codebase and git history. Checks for stale references, broken examples, missing sections, inaccurate claims, and undocumented features.
- **Input:** No file list — it always targets those three specific doc files. Uses `git ls-files`, `git log`, `git tag`, and reads `pyproject.toml` for context.
- **Repo scope:** Always the same three files. Runs once per repo.
- **Tools:** Read, Glob, Grep, git commands via Bash (read-only)

### 4. `python_characterization_tester`
- **Language:** Python-specific
- **What it does:** Writes characterization tests that lock current behavior for uncovered code. Maximizes line coverage. Never modifies source — only creates/edits test files.
- **Input:** A list of source file paths + import context + optional uncovered-lines data. Gets coverage data via `pytest --cov` at start.
- **Repo scope:** Runs on a provided set of Python source files. Writes into `tests/`.
- **Tools:** Read, Edit (tests/* only), Write (tests/* only), Glob, Grep

### 5. `python_implementer`
- **Language:** Python-specific
- **What it does:** Implements features from an approved plan using TDD. Reads the plan, writes failing tests first, then implements. Auto-lints with ruff after edits, runs pytest + pyright on completion.
- **Input:** An approved plan passed in the prompt (no file list — it discovers files from the plan).
- **Repo scope:** Touches whatever files the plan specifies. Can create and modify any file.
- **Tools:** Read, Glob, Grep, Edit, Write

### 6. `python_structural_refactorer`
- **Language:** Python-specific
- **What it does:** Executes scoped structural refactors: breaking circular deps, fixing layer violations, splitting god modules, extracting shared code, removing dead code, or renaming. Has specific instructions per refactor type.
- **Input:** A list of files to modify + a problem description + a refactor type (one of: `circular_deps`, `layering`, `god_modules`, `extract_shared`, `dead_code`, `naming`) + relevant test files.
- **Repo scope:** Only touches the listed files (can create new ones for extractions). Runs scoped tests on completion.
- **Tools:** Read, Glob, Grep, Edit, Write

### 7. `fixer`
- **Language:** Python-specific (uses ruff + pyright hooks)
- **What it does:** Takes a list of findings/items (from any reviewer) and applies the fixes. Auto-lints after edits, runs ruff + pyright on completion.
- **Input:** A list of finding objects (any shape — uses a formatter to render them). No file list directly; files come from the findings.
- **Repo scope:** Only modifies files referenced by the findings.
- **Tools:** Read, Edit, Write, Grep

### 8. `spec_compliance_reviewer`
- **Language:** Language-agnostic (though typically used on Python projects)
- **What it does:** Compares an implementation against its spec/plan. Checks completeness (was every step built?), scope creep (unplanned changes), contract compliance, behavioral fidelity, and test coverage.
- **Input:** A spec (title, description, steps with file lists) + implementation files + unplanned files.
- **Repo scope:** Reads the listed implementation files. Read-only.
- **Tools:** Read, Grep (read-only)

### 9. `triage`
- **Language:** Language-agnostic
- **What it does:** Interactive selection agent. Presents a numbered list of items to the user, interprets natural-language selection ("all the high ones", "skip low severity"), and returns the selected indices. Used between review and fix stages.
- **Input:** A list of items (findings, tasks, etc.) + user's natural-language selection.
- **Repo scope:** Doesn't touch any files. Pure selection/filtering.
- **Tools:** None

## Summary

| Agent | Python-specific? | Input type | Repo scope |
|---|---|---|---|
| `python_reviewer` | Yes | Single .py file | One file at a time |
| `architecture_reviewer` | Yes (AST) | Batch of files + summaries | Cross-file analysis |
| `docs_reviewer` | No | None (fixed targets) | README, CHANGELOG, CLAUDE.md |
| `python_characterization_tester` | Yes | Source files + coverage | Writes tests for listed files |
| `python_implementer` | Yes | Plan (in prompt) | Whatever the plan specifies |
| `python_structural_refactorer` | Yes | Files + problem + type | Only listed files |
| `fixer` | Yes (ruff/pyright) | List of findings | Files from findings |
| `spec_compliance_reviewer` | No | Spec + file lists | Reads listed files |
| `triage` | No | Any list of items | No files (interactive filter) |
