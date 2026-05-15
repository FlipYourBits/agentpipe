# Per-File Audit Code Fixes

Refactor audit workflow Phase 3b from a single monolithic code writer agent into parallel per-file agents with granular state tracking.

## Motivation

The current Phase 3b sends all code findings to a single `python_code_writer` agent as one plan. This has three problems:

1. **No resume granularity** — if the agent crashes mid-way through fixing 200 findings, all progress is lost and the entire phase restarts.
2. **System prompt too large** — 200+ findings embedded in the system prompt can exceed OS argument limits (ARG_MAX).
3. **No parallelism** — one agent does all the work sequentially.

Phase 3a (coverage fixes) already solves all three problems by running one `test_writer` agent per file with `state.task_done()` tracking. This spec applies the same pattern to Phase 3b.

## Design

### Grouping findings by file

Findings are grouped by their primary file (`finding.files[0]`). Findings that reference multiple files are separated into a cross-file group.

```python
single_file: dict[str, list[UnifiedFinding]] = {}
cross_file: list[UnifiedFinding] = []

for f in code_selected:
    if len(f.files) > 1:
        cross_file.append(f)
    else:
        single_file.setdefault(f.files[0], []).append(f)
```

### State tracking

Phase 3b adopts the same state pattern as Phase 3a:

```python
# Initialize phase (only if not already in code_fixes from a previous partial run)
if state.phase != "code_fixes":
    file_keys = list(single_file.keys()) + [f"_cross_{i}" for i in range(len(cross_file_groups))]
    state.phase = "code_fixes"
    state.pending = file_keys
    state.completed = {}
    state.save()

# After each agent completes
state.task_done(file_key, {
    "files_created": result.output.files_created,
    "files_modified": result.output.files_modified,
    "summary": result.output.summary,
    "cost": result.cost_usd,
    "error": result.error,
})
```

On resume, files already in `state.completed` are skipped. Only `state.pending` files get new agent runs.

### Per-file agent construction

Each per-file agent gets a focused plan containing only that file's findings, plus the file content for context:

```python
for file_path, file_findings in single_file.items():
    if file_path not in state.pending:
        continue  # already completed in previous run

    plan_items = []
    for f in file_findings:
        item = f"[{f.source}] {f.title}\n{f.description}"
        if f.suggestion:
            item += f"\nSuggestion: {f.suggestion}"
        plan_items.append(item)

    plan = f"Fix the following issues in `{file_path}`:\n\n" + "\n\n---\n\n".join(plan_items)
    agent = make_python_code_writer(plan=plan, config=config)
    # run via run_limited (same as Phase 1 and 3a)
```

The agent uses `make_python_code_writer` unchanged — same tools, hooks, and structured output. Each agent independently runs lint (PostToolUse) and tests+typecheck (Stop hooks).

### Parallel execution

Uses the existing `sem = asyncio.Semaphore(max_parallel)` and `run_limited()` helper, same as Phase 1 analysis agents and Phase 3a coverage agents:

```python
fix_tasks = []
for file_path, file_findings in single_file.items():
    if file_path not in state.pending:
        continue
    agent = make_python_code_writer(plan=..., config=config)
    fix_tasks.append(run_limited(agent, "Fix the issues described in the plan.", file_path))

if fix_tasks:
    fix_results = await asyncio.gather(*fix_tasks)
```

### Cross-file findings

Cross-file findings (those with `len(files) > 1`) run in a second pass after all single-file agents complete. They are grouped by their sorted file set to batch related findings:

```python
cross_groups: dict[tuple[str, ...], list[UnifiedFinding]] = {}
for f in cross_file:
    key = tuple(sorted(f.files))
    cross_groups.setdefault(key, []).append(f)
```

Each group gets its own agent with a plan that names all involved files. These also run in parallel with the semaphore, tracked in state with `_cross_0`, `_cross_1`, etc. as keys.

### No iteration loop

The current iteration loop (show diff, prompt for feedback, re-run) is removed. Audit findings are already prescriptive — the agent either fixes them or doesn't. If fixes need manual adjustment afterward, that happens in an interactive Claude Code session, not in the audit pipeline.

### Result aggregation

After all agents complete, results are merged into a single `CodeWriterResult`:

```python
all_created = []
all_modified = []
all_skipped = []
failed_files = []

for file_key, saved in state.completed.items():
    if saved.get("error"):
        failed_files.append(file_key)
    else:
        all_created.extend(saved.get("files_created", []))
        all_modified.extend(saved.get("files_modified", []))

final_result = CodeWriterResult(
    files_created=all_created,
    files_modified=all_modified,
    skipped_items=failed_files,
    summary=f"Fixed {len(state.completed) - len(failed_files)}/{len(state.completed)} files",
)
```

Failed files are logged but don't block the workflow. The state preserves which files failed so a re-run only retries those.

### Progress display

Each completed agent prints a one-line status, same as Phase 3a:

```
  DONE codemonkeys/core/hooks.py: 3 finding(s) fixed
  FAIL codemonkeys/core/runner.py: Agent error
  (3/15)
```

The existing `_agent_done` / `_agent_total` counter in `run_limited` handles this.

## Files changed

- `codemonkeys/workflows/audit.py` — replace Phase 3b monolithic loop with per-file parallel agents + cross-file second pass
- No changes to `codemonkeys/agents/python_code_writer.py` — `make_python_code_writer` already accepts a string plan
- No changes to `codemonkeys/core/state.py` — existing `task_done` / `finish_phase` API is sufficient

## What this does NOT change

- Phase 1 (analysis), Phase 2 (triage), Phase 3a (coverage), Phase 4 (docs & commit) are untouched
- The `make_python_code_writer` agent definition stays the same
- The `run_limited` helper stays the same
- The feature/bugfix workflows keep their iteration loops
