# Agent Audit Corpus

A minimal test corpus of intentionally buggy Python files and stale docs, plus a harness script that runs all 11 codemonkeys agents against it and saves structured results for comparison.

## Directory Structure

```
audit/
  corpus/
    tasklib/
      __init__.py
      models.py
      manager.py
      db.py
      utils.py
    tests/
      test_tasks.py
    README.md
    CHANGELOG.md
    docs/
      spec.md
      plan.md
  run_audit.py
  results/                # created at runtime
```

## Corpus Design

The corpus pretends to be "tasklib" — a small task manager library. Every file contains intentional bugs, smells, or inaccuracies designed to trigger specific agents.

### `tasklib/__init__.py`

Exports from the package. Re-exports a symbol that doesn't exist to trigger import-level findings.

### `tasklib/models.py` (~25 lines)

Data models for Task and User.

Planted problems:
- **Mutable default argument**: `def __init__(self, tags: list = [])` — classic Python bug
- **Silent type coercion**: `__init__` converts strings to int without validation or error
- **Missing `__hash__`**: instances used as dict keys in manager.py but no `__hash__` defined
- **No `__eq__`**: equality comparison used in tests but relies on default identity semantics

Target agents:
- **python_reviewer**: code quality (mutable default, missing dunder methods)
- **characterization_tester**: testable logic with no test coverage
- **fixer**: mutable default is mechanically fixable

### `tasklib/manager.py` (~40 lines)

TaskManager class — a god module that does everything.

Planted problems:
- **God module**: CRUD, validation, notification (print), formatting, and file I/O persistence all in one class
- **Global mutable state**: `_tasks: dict = {}` at module level, accessed by TaskManager methods
- **Bare `except:` clauses**: catches and silently ignores all exceptions in save/load
- **Hardcoded file path**: `TASKS_FILE = "/tmp/tasks.json"` for persistence
- **No input validation**: accepts any type for task fields without checking
- **Imports from utils**: `from tasklib.utils import proc` — completes the circular dependency with utils.py

Target agents:
- **python_reviewer**: code quality (bare except, global state), resilience (hardcoded path, no validation)
- **architecture_reviewer**: SRP violation, tight coupling to db.py and utils.py, circular dep with utils
- **structural_refactorer**: god_modules refactor type
- **characterization_tester**: untested CRUD logic

### `tasklib/db.py` (~25 lines)

Database layer with sqlite3.

Planted problems:
- **SQL injection**: query built with f-string formatting (`f"SELECT * FROM tasks WHERE id = {task_id}"`)
- **Hardcoded credentials**: `DB_PASSWORD = "admin123"` at module level
- **Resource leak**: `sqlite3.connect()` called but connection never closed (no context manager, no `finally`)
- **Swallowed exceptions**: `except Exception: pass` around all database operations

Target agents:
- **python_reviewer**: security (SQL injection, hardcoded creds), resilience (resource leak, swallowed exceptions)
- **architecture_reviewer**: no abstraction layer, raw SQL mixed with business logic
- **fixer**: SQL injection and resource leak are fixable

### `tasklib/utils.py` (~20 lines)

Utility functions.

Planted problems:
- **Circular import**: `from tasklib.manager import TaskManager` at top level (manager also imports utils)
- **Dead code**: two functions (`_legacy_format`, `_unused_helper`) never called anywhere
- **Bad naming**: single-letter variables (`d`, `x`, `t`), unclear function name (`proc`)
- **Unnecessary complexity**: one-liner comprehension that should be a readable loop

Target agents:
- **python_reviewer**: code quality (naming, dead code, complexity)
- **architecture_reviewer**: circular dependency between utils and manager
- **structural_refactorer**: circular_deps and dead_code refactor types

### `tests/test_tasks.py` (~25 lines)

Test file with intentionally weak tests.

Planted problems:
- **Over-mocking**: patches db, filesystem, and model internals — tests prove nothing about real behavior
- **Vacuous assertions**: `assert True`, `assert result is not None`, `assert isinstance(result, dict)`
- **Unfailable test**: one test that can never fail regardless of code behavior
- **No edge cases**: only tests the happy path with hardcoded values
- **Magic numbers**: `assert len(result) == 3` with no explanation of why 3

Target agents:
- **python_reviewer**: test quality checklist (weak assertions, over-mocking)
- **characterization_tester**: poor coverage baseline to improve upon

### `README.md` (~30 lines)

Stale/wrong project documentation.

Planted problems:
- **Wrong install command**: claims `pip install tasklib` — no setup.py or pyproject.toml exists
- **Phantom CLI**: documents `tasklib run --all` command that doesn't exist
- **Wrong API example**: shows `manager.get_by_priority()` — method doesn't exist
- **False coverage claim**: "100% test coverage" — not true
- **False async claim**: "fully async support" — nothing in the code is async

Target agents:
- **readme_reviewer**: every verifiable claim is wrong

### `CHANGELOG.md` (~20 lines)

Changelog that doesn't match reality.

Planted problems:
- **Phantom release**: lists v2.0.0 "async rewrite" that never happened
- **False fix claim**: v1.1.0 "fixed SQL injection vulnerability" — still present in db.py
- **Missing entries**: actual code changes (e.g., utils.py additions) have no changelog entry
- **Wrong dates**: dates don't align with any actual commit history

Target agents:
- **changelog_reviewer**: mismatch between changelog entries and git history/code state

### `docs/spec.md` (~30 lines)

Feature specification for tasklib.

Specifies 5 features:
1. CRUD operations — partially implemented (buggy)
2. Tagging system — partially implemented (mutable default bug)
3. Priority sorting — not implemented at all
4. Email notifications — not implemented (manager just prints)
5. Export to JSON — not implemented

Target agents:
- **spec_compliance_reviewer**: steps_implemented < steps_total, can identify which features are missing vs. partial vs. wrong

### `docs/plan.md` (~20 lines)

Small implementation plan: "Add `export_json()` method to TaskManager with tests."

Steps:
1. Add `export_json(path: str)` method to TaskManager
2. Write tests for export_json in test_tasks.py
3. Update README with export documentation

Deliberately simple so python_implementer finishes quickly during audit runs.

Target agents:
- **python_implementer**: concrete plan to execute via TDD

## Agent Coverage Matrix

| Agent | Inputs | What It Exercises |
|-------|--------|-------------------|
| python_reviewer | models.py, manager.py, db.py, utils.py, test_tasks.py | Code quality, security, resilience, test quality checklists |
| architecture_reviewer | all 4 tasklib modules | SRP violations, circular deps, coupling, missing abstractions |
| review_auditor | python_reviewer RunResult(s) | Tool compliance, file coverage, finding quality |
| triage | combined findings from reviewers | Selection/filtering of findings |
| fixer | triaged findings | Applying mechanical fixes (SQL injection, mutable defaults, bare excepts) |
| structural_refactorer | manager.py (god_modules), utils.py (circular_deps) | Targeted refactoring with type-specific instructions |
| characterization_tester | all 4 tasklib modules | Generate tests for uncovered code |
| readme_reviewer | README.md | Verify claims against actual codebase |
| changelog_reviewer | CHANGELOG.md | Verify entries against git history |
| spec_compliance_reviewer | spec.md + all corpus files | Check implementation vs. specification |
| python_implementer | plan.md | TDD implementation of a small feature |

## Harness: `run_audit.py`

A single async Python script.

### Phases

**Phase 1 — Primary reviews (parallel):**
- python_reviewer on tasklib modules + test file (batched per existing logic)
- architecture_reviewer on the 4 tasklib modules
- readme_reviewer pointed at corpus README.md
- changelog_reviewer pointed at corpus CHANGELOG.md

**Phase 2 — Downstream (sequential, depends on Phase 1):**
- review_auditor on each python_reviewer RunResult
- triage on combined findings (auto-selects "all high severity" to avoid interactive prompt)
- fixer on triaged findings

**Phase 3 — Standalone (parallel):**
- structural_refactorer on manager.py (god_modules) and utils.py (circular_deps)
- characterization_tester on the tasklib modules
- spec_compliance_reviewer with spec.md vs. corpus files
- python_implementer with plan.md

### Corpus Isolation

The harness copies the corpus to a temporary directory before running. This prevents fixer and implementer from modifying the originals. The tempdir is cleaned up after the run.

### Output

**Live:** Rich terminal output via the existing event handler system.

**Saved:** One JSON file per agent run to `audit/results/<YYYY-MM-DDTHH-MM-SS>/`:

```
python_reviewer_batch0.json
python_reviewer_batch1.json
architecture_reviewer.json
readme_reviewer.json
changelog_reviewer.json
review_auditor_batch0.json
review_auditor_batch1.json
triage.json
fixer.json
structural_refactorer_god.json
structural_refactorer_circular.json
characterization_tester.json
spec_compliance_reviewer.json
python_implementer.json
summary.json
```

Each JSON file contains:
- `agent_name`: agent identifier
- `model`: model used
- `output`: full Pydantic structured output (serialized)
- `events`: event trace (tool calls, text output, check results)
- `tokens`: input/output token counts
- `cost_usd`: estimated cost
- `duration_seconds`: wall clock time

`summary.json` is a roll-up with one entry per agent: name, model, tokens, cost, duration, and whether the agent produced output without error.
