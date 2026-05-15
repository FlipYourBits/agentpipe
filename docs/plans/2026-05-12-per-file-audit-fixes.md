# Per-File Audit Code Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the monolithic Phase 3b code writer with parallel per-file agents that track completion in workflow state for granular resume.

**Architecture:** Group code findings by primary file, dispatch one `python_code_writer` agent per file using the existing semaphore and `asyncio.gather`, track each file's completion via `state.task_done()`. Cross-file findings run in a second pass. The iteration loop is removed.

**Tech Stack:** Python 3.12, asyncio, existing `WorkflowState`, existing `make_python_code_writer`

**Spec:** `docs/specs/2026-05-12-per-file-audit-fixes-design.md`

---

### File Map

- **Modify:** `codemonkeys/workflows/audit.py` — Phase 3b replacement (lines 566–654)
- **Test:** `tests/test_audit_fix_grouping.py` — unit tests for grouping + result aggregation logic

---

### Task 1: Extract grouping helper functions

Extract the finding grouping and result aggregation logic into testable helper functions at module level in `audit.py`. This keeps Phase 3b's inline code clean and lets us test grouping without mocking the whole workflow.

**Files:**
- Modify: `codemonkeys/workflows/audit.py` (add functions above `run_audit`)

- [ ] **Step 1: Write the failing test for single-file grouping**

Create `tests/test_audit_fix_grouping.py`:

```python
"""Tests for audit fix grouping and result aggregation."""

import pytest

from codemonkeys.workflows.audit import UnifiedFinding, _group_findings_by_file


def _finding(files: list[str], title: str = "test") -> UnifiedFinding:
    return UnifiedFinding(
        source="review",
        severity="medium",
        title=title,
        description="desc",
        files=files,
    )


class TestGroupFindingsByFile:
    def test_single_file_findings_grouped_by_path(self):
        findings = [
            _finding(["src/a.py"], "fix a1"),
            _finding(["src/a.py"], "fix a2"),
            _finding(["src/b.py"], "fix b1"),
        ]
        single, cross = _group_findings_by_file(findings)
        assert set(single.keys()) == {"src/a.py", "src/b.py"}
        assert len(single["src/a.py"]) == 2
        assert len(single["src/b.py"]) == 1
        assert cross == []

    def test_multi_file_findings_go_to_cross_file(self):
        findings = [
            _finding(["src/a.py"]),
            _finding(["src/a.py", "src/b.py"]),
        ]
        single, cross = _group_findings_by_file(findings)
        assert set(single.keys()) == {"src/a.py"}
        assert len(cross) == 1
        assert cross[0].files == ["src/a.py", "src/b.py"]

    def test_empty_input(self):
        single, cross = _group_findings_by_file([])
        assert single == {}
        assert cross == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_fix_grouping.py -v`
Expected: ImportError — `_group_findings_by_file` does not exist yet.

- [ ] **Step 3: Implement `_group_findings_by_file`**

Add this function in `codemonkeys/workflows/audit.py`, after the `_format_finding` function (after line 271):

```python
def _group_findings_by_file(
    findings: list[UnifiedFinding],
) -> tuple[dict[str, list[UnifiedFinding]], list[UnifiedFinding]]:
    """Split findings into per-file groups and cross-file findings.

    Returns (single_file_map, cross_file_list).
    """
    single: dict[str, list[UnifiedFinding]] = {}
    cross: list[UnifiedFinding] = []
    for f in findings:
        if len(f.files) > 1:
            cross.append(f)
        else:
            single.setdefault(f.files[0], []).append(f)
    return single, cross
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_fix_grouping.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add codemonkeys/workflows/audit.py tests/test_audit_fix_grouping.py
git commit -m "feat: add _group_findings_by_file helper for per-file audit fixes"
```

---

### Task 2: Add cross-file grouping helper

Group cross-file findings by their sorted file set so related findings are batched together.

**Files:**
- Modify: `codemonkeys/workflows/audit.py`
- Modify: `tests/test_audit_fix_grouping.py`

- [ ] **Step 1: Write the failing test for cross-file grouping**

Add to `tests/test_audit_fix_grouping.py`:

```python
from codemonkeys.workflows.audit import _group_cross_file_findings


class TestGroupCrossFileFindings:
    def test_groups_by_sorted_file_set(self):
        findings = [
            _finding(["src/b.py", "src/a.py"], "fix 1"),
            _finding(["src/a.py", "src/b.py"], "fix 2"),
            _finding(["src/c.py", "src/d.py"], "fix 3"),
        ]
        groups = _group_cross_file_findings(findings)
        assert len(groups) == 2
        key_ab = ("src/a.py", "src/b.py")
        key_cd = ("src/c.py", "src/d.py")
        assert len(groups[key_ab]) == 2
        assert len(groups[key_cd]) == 1

    def test_empty_input(self):
        groups = _group_cross_file_findings([])
        assert groups == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_fix_grouping.py::TestGroupCrossFileFindings -v`
Expected: ImportError — `_group_cross_file_findings` does not exist yet.

- [ ] **Step 3: Implement `_group_cross_file_findings`**

Add this function in `codemonkeys/workflows/audit.py`, right after `_group_findings_by_file`:

```python
def _group_cross_file_findings(
    findings: list[UnifiedFinding],
) -> dict[tuple[str, ...], list[UnifiedFinding]]:
    """Group cross-file findings by their sorted file set."""
    groups: dict[tuple[str, ...], list[UnifiedFinding]] = {}
    for f in findings:
        key = tuple(sorted(f.files))
        groups.setdefault(key, []).append(f)
    return groups
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_fix_grouping.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add codemonkeys/workflows/audit.py tests/test_audit_fix_grouping.py
git commit -m "feat: add _group_cross_file_findings helper"
```

---

### Task 3: Add result aggregation helper

Extract the logic that merges per-file agent results into a single `CodeWriterResult`.

**Files:**
- Modify: `codemonkeys/workflows/audit.py`
- Modify: `tests/test_audit_fix_grouping.py`

- [ ] **Step 1: Write the failing test for result aggregation**

Add to `tests/test_audit_fix_grouping.py`:

```python
from codemonkeys.workflows.audit import _aggregate_fix_results
from codemonkeys.agents.python_code_writer import CodeWriterResult


class TestAggregateFixResults:
    def test_merges_successful_results(self):
        completed = {
            "src/a.py": {
                "files_created": ["tests/test_a.py"],
                "files_modified": ["src/a.py"],
                "summary": "fixed a",
            },
            "src/b.py": {
                "files_created": [],
                "files_modified": ["src/b.py"],
                "summary": "fixed b",
            },
        }
        result = _aggregate_fix_results(completed)
        assert result.files_created == ["tests/test_a.py"]
        assert set(result.files_modified) == {"src/a.py", "src/b.py"}
        assert result.skipped_items == []
        assert "2/2" in result.summary

    def test_failed_files_go_to_skipped(self):
        completed = {
            "src/a.py": {
                "files_created": [],
                "files_modified": ["src/a.py"],
                "summary": "fixed a",
            },
            "src/b.py": {
                "error": "agent crashed",
            },
        }
        result = _aggregate_fix_results(completed)
        assert result.files_modified == ["src/a.py"]
        assert result.skipped_items == ["src/b.py"]
        assert "1/2" in result.summary

    def test_empty_completed(self):
        result = _aggregate_fix_results({})
        assert result.files_created == []
        assert result.files_modified == []
        assert result.skipped_items == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_fix_grouping.py::TestAggregateFixResults -v`
Expected: ImportError — `_aggregate_fix_results` does not exist yet.

- [ ] **Step 3: Implement `_aggregate_fix_results`**

Add this function in `codemonkeys/workflows/audit.py`, right after `_group_cross_file_findings`:

```python
def _aggregate_fix_results(completed: dict[str, dict]) -> CodeWriterResult:
    """Merge per-file state.completed entries into a single CodeWriterResult."""
    all_created: list[str] = []
    all_modified: list[str] = []
    failed: list[str] = []
    for key, saved in completed.items():
        if saved.get("error"):
            failed.append(key)
        else:
            all_created.extend(saved.get("files_created", []))
            all_modified.extend(saved.get("files_modified", []))
    succeeded = len(completed) - len(failed)
    return CodeWriterResult(
        files_created=all_created,
        files_modified=all_modified,
        skipped_items=failed,
        summary=f"Fixed {succeeded}/{len(completed)} file groups",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_fix_grouping.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add codemonkeys/workflows/audit.py tests/test_audit_fix_grouping.py
git commit -m "feat: add _aggregate_fix_results helper"
```

---

### Task 4: Add `_build_file_plan` helper

Extract the per-file plan string construction so it's testable and reusable for both single-file and cross-file agents.

**Files:**
- Modify: `codemonkeys/workflows/audit.py`
- Modify: `tests/test_audit_fix_grouping.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_audit_fix_grouping.py`:

```python
from codemonkeys.workflows.audit import _build_file_plan


class TestBuildFilePlan:
    def test_single_file_plan(self):
        findings = [
            UnifiedFinding(
                source="review", severity="high", title="bug in foo",
                description="foo returns wrong value", files=["src/a.py"],
                suggestion="return correct value",
            ),
        ]
        plan = _build_file_plan("src/a.py", findings)
        assert "src/a.py" in plan
        assert "bug in foo" in plan
        assert "foo returns wrong value" in plan
        assert "return correct value" in plan

    def test_multiple_files_listed(self):
        findings = [
            _finding(["src/a.py", "src/b.py"], "cross fix"),
        ]
        plan = _build_file_plan(["src/a.py", "src/b.py"], findings)
        assert "src/a.py" in plan
        assert "src/b.py" in plan

    def test_no_suggestion_omitted(self):
        findings = [
            UnifiedFinding(
                source="review", severity="low", title="minor",
                description="desc", files=["src/a.py"], suggestion=None,
            ),
        ]
        plan = _build_file_plan("src/a.py", findings)
        assert "Suggestion" not in plan
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_fix_grouping.py::TestBuildFilePlan -v`
Expected: ImportError — `_build_file_plan` does not exist yet.

- [ ] **Step 3: Implement `_build_file_plan`**

Add this function in `codemonkeys/workflows/audit.py`, right after `_aggregate_fix_results`:

```python
def _build_file_plan(
    files: str | list[str],
    findings: list[UnifiedFinding],
) -> str:
    """Build a plan string for one code_writer agent from findings."""
    if isinstance(files, str):
        header = f"Fix the following issues in `{files}`:"
    else:
        paths = ", ".join(f"`{f}`" for f in files)
        header = f"Fix the following cross-file issues in {paths}:"
    items = []
    for f in findings:
        item = f"[{f.source}] {f.title}\n{f.description}"
        if f.suggestion:
            item += f"\nSuggestion: {f.suggestion}"
        items.append(item)
    return header + "\n\n" + "\n\n---\n\n".join(items)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_fix_grouping.py -v`
Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add codemonkeys/workflows/audit.py tests/test_audit_fix_grouping.py
git commit -m "feat: add _build_file_plan helper"
```

---

### Task 5: Replace Phase 3b with per-file parallel agents

Replace the monolithic iteration loop (lines 566–654) with the new per-file parallel approach.

**Files:**
- Modify: `codemonkeys/workflows/audit.py:566-654`

- [ ] **Step 1: Remove unused imports**

The iteration loop used `generate_patch`, `snapshot`, `IterationAction`, and `prompt_iteration`. Check if these are still used elsewhere in the file before removing. `generate_patch` and `snapshot` are also used in Phase 3a (coverage) — keep them. `IterationAction` and `prompt_iteration` are only used in Phase 3b — remove their import.

In `codemonkeys/workflows/audit.py`, remove line 57:
```python
from codemonkeys.core.iteration import IterationAction, prompt_iteration
```

- [ ] **Step 2: Replace Phase 3b code block**

Replace everything from the `# --- Phase 3b:` comment (line 566) through the result aggregation block (ending at line 654, just before `# --- Phase 4:`) with the new implementation:

```python
    # --- Phase 3b: Code fixes (per-file, parallel) ---
    final_result: CodeWriterResult | None = None
    code_fix_failed = False
    if code_selected:
        single_file, cross_file = _group_findings_by_file(code_selected)
        cross_groups = _group_cross_file_findings(cross_file)
        total_groups = len(single_file) + len(cross_groups)

        _console.print()
        _console.rule(
            f"[3/4] Fixing {len(code_selected)} finding(s) across {total_groups} file group(s)",
            style="bold green",
        )

        if resuming and "code_fixes" in state.phases_done:
            fix_data = state.phases_done["code_fixes"]
            final_result = _aggregate_fix_results(fix_data.get("completed", {}))
            _console.print(f"[dim]Restored code fix results from previous run[/dim]")
        else:
            # Initialize phase state (only if not resuming a partial code_fixes run)
            if state.phase != "code_fixes":
                cross_keys = [f"_cross_{i}" for i in range(len(cross_groups))]
                state.phase = "code_fixes"
                state.pending = list(single_file.keys()) + cross_keys
                state.completed = {}
                state.save()

            _agent_done = 0
            _agent_total = total_groups

            async def run_fix(agent, prompt, task_key):
                nonlocal _agent_done
                async with sem:
                    with logged(log_dir, f"{agent.name}:{task_key}", printer=printer) as evt:
                        result = await run_agent(agent, prompt, on_event=evt, log_dir=log_dir)
                saved = {
                    "files_created": result.output.files_created if isinstance(result.output, CodeWriterResult) else [],
                    "files_modified": result.output.files_modified if isinstance(result.output, CodeWriterResult) else [],
                    "summary": result.output.summary if isinstance(result.output, CodeWriterResult) else "",
                    "cost": result.cost_usd,
                }
                if result.error:
                    saved["error"] = result.error
                    _console.print(f"  [red]FAIL {task_key}: {result.error}[/red]")
                state.task_done(task_key, saved)
                _agent_done += 1
                _console.print(f"  [dim]({_agent_done}/{_agent_total})[/dim]")
                return result

            # Pass 1: single-file fixes
            fix_tasks = []
            for file_path, file_findings in single_file.items():
                if file_path not in state.pending:
                    continue
                plan = _build_file_plan(file_path, file_findings)
                agent = make_python_code_writer(plan=plan, config=config)
                fix_tasks.append(run_fix(agent, "Fix the issues described in the plan.", file_path))

            if fix_tasks:
                await asyncio.gather(*fix_tasks)

            # Pass 2: cross-file fixes
            cross_tasks = []
            for i, (file_set, group_findings) in enumerate(cross_groups.items()):
                cross_key = f"_cross_{i}"
                if cross_key not in state.pending:
                    continue
                plan = _build_file_plan(list(file_set), group_findings)
                agent = make_python_code_writer(plan=plan, config=config)
                cross_tasks.append(run_fix(agent, "Fix the issues described in the plan.", cross_key))

            if cross_tasks:
                await asyncio.gather(*cross_tasks)

            final_result = _aggregate_fix_results(state.completed)
            failed_count = len(final_result.skipped_items)
            if failed_count:
                code_fix_failed = True
                _console.print(
                    f"\n[yellow]{failed_count} file group(s) failed — "
                    f"state preserved for resume.[/yellow]"
                )

            state.finish_phase("code_fixes", {"completed": state.completed})

    if final_result is None and test_files_created:
        final_result = CodeWriterResult(
            summary=f"Tests written for {len(test_files_created)} file(s)",
            files_created=test_files_created,
            files_modified=[],
        )
    elif final_result and test_files_created:
        final_result = CodeWriterResult(
            summary=final_result.summary,
            files_created=final_result.files_created + test_files_created,
            files_modified=final_result.files_modified,
        )

    if code_fix_failed and not test_files_created and final_result and not final_result.files_modified:
        _console.print(
            "\n[yellow]All code fixes failed — state preserved for resume. "
            "Re-run to retry.[/yellow]"
        )
        return None
```

- [ ] **Step 3: Update the module docstring**

Replace line 7 `code findings -> code_writer (iteration loop)` with:

```python
        code findings -> code_writer (per-file, parallel)
```

- [ ] **Step 4: Run lint and type check**

Run: `uv run ruff check codemonkeys/workflows/audit.py && uv run pyright codemonkeys/workflows/audit.py`
Expected: No new errors from our changes (pre-existing errors on other lines are OK).

- [ ] **Step 5: Run all tests**

Run: `uv run pytest tests/test_audit_fix_grouping.py tests/test_integration.py tests/test_python_code_reviewer.py tests/test_python_architecture_reviewer.py -v`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add codemonkeys/workflows/audit.py
git commit -m "feat: replace monolithic Phase 3b with parallel per-file code fixers"
```

---

### Task 6: Verify `subprocess` import is still needed

After removing the iteration loop, the only `subprocess` usage in `run_audit` was `subprocess.run(["git", "checkout", "."])` in the `QUIT` branch. Check whether `subprocess` is still used elsewhere in the file.

**Files:**
- Modify: `codemonkeys/workflows/audit.py`

- [ ] **Step 1: Check subprocess usage**

Run: `grep -n 'subprocess' codemonkeys/workflows/audit.py`

If the only hit is the import line, remove it. If other uses exist (e.g. `_get_diff_files` on line 76), keep it.

`_get_diff_files` uses `subprocess.run` on line 76, so the import stays.

- [ ] **Step 2: Verify no unused imports remain**

Run: `uv run ruff check codemonkeys/workflows/audit.py --select F401`
Expected: No unused import errors. If `IterationAction` or `prompt_iteration` show up, remove them.

- [ ] **Step 3: Commit if any changes**

```bash
git add codemonkeys/workflows/audit.py
git commit -m "chore: remove unused imports from audit workflow"
```
