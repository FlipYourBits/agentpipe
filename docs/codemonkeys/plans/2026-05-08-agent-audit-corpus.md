# Agent Audit Corpus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a test corpus of intentionally buggy Python files and a harness that runs all 11 codemonkeys agents against it, saving per-agent JSON results for comparison.

**Architecture:** A self-contained `audit/` directory with a fake "tasklib" project (4 Python modules, 1 test file, stale docs) and a `run_audit.py` harness. The harness copies the corpus to a tempdir with git initialized, strips agent hooks (audit tests agent logic, not CI checks), runs agents in 3 phases, and saves per-agent JSON results.

**Tech Stack:** Python 3.12+, asyncio, codemonkeys agent SDK, Rich (terminal output)

**Spec:** `docs/codemonkeys/specs/2026-05-08-agent-audit-corpus-design.md`

---

### Task 1: Create corpus Python source files

**Files:**
- Create: `audit/corpus/tasklib/__init__.py`
- Create: `audit/corpus/tasklib/models.py`
- Create: `audit/corpus/tasklib/db.py`
- Create: `audit/corpus/tasklib/manager.py`
- Create: `audit/corpus/tasklib/utils.py`
- Create: `audit/corpus/pyproject.toml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p audit/corpus/tasklib
```

- [ ] **Step 2: Write `audit/corpus/pyproject.toml`**

Minimal project config so the corpus is a valid Python project:

```toml
[project]
name = "tasklib"
version = "1.0.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"

[tool.pyright]
include = ["tasklib"]
```

- [ ] **Step 3: Write `audit/corpus/tasklib/models.py`**

Planted bugs: mutable default argument, silent type coercion, no `__hash__`/`__eq__`.

```python
class Task:
    def __init__(self, task_id, title, tags=[], status="pending"):
        self.task_id = int(task_id)
        self.title = title
        self.tags = tags
        self.status = status
        self.done = False

    def mark_done(self):
        self.done = True
        self.status = "done"
        return self

    def as_dict(self):
        return {
            "id": self.task_id,
            "title": self.title,
            "tags": self.tags,
            "status": self.status,
        }


class User:
    def __init__(self, name, role="member"):
        self.name = name
        self.role = role
```

- [ ] **Step 4: Write `audit/corpus/tasklib/db.py`**

Planted bugs: SQL injection via f-string, hardcoded credentials, resource leaks, swallowed exceptions.

```python
import sqlite3

DB_PASSWORD = "admin123"
DB_PATH = "/tmp/tasklib.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def find_task(task_id):
    conn = get_connection()
    try:
        cursor = conn.execute(f"SELECT * FROM tasks WHERE id = {task_id}")
        return cursor.fetchone()
    except Exception:
        pass


def save_task(task_id, title):
    conn = get_connection()
    try:
        conn.execute(f"INSERT INTO tasks VALUES ({task_id}, '{title}')")
        conn.commit()
    except Exception:
        pass
```

- [ ] **Step 5: Write `audit/corpus/tasklib/manager.py`**

Planted bugs: god module (CRUD + persistence + formatting), global mutable state, bare `except:`, hardcoded path, no validation, circular dep with utils.

```python
import json

from tasklib.models import Task
from tasklib.utils import proc

TASKS_FILE = "/tmp/tasks.json"
_tasks: dict = {}


class TaskManager:
    def add(self, title, tags=[]):
        task = Task(len(_tasks) + 1, title, tags)
        _tasks[task] = task.title
        return task

    def get(self, task_id):
        for t in _tasks:
            if t.task_id == task_id:
                return t
        return None

    def remove(self, task_id):
        task = self.get(task_id)
        if task:
            del _tasks[task]

    def list_all(self):
        return list(_tasks.keys())

    def save(self):
        try:
            data = {str(t.task_id): t.title for t in _tasks}
            with open(TASKS_FILE, "w") as f:
                json.dump(data, f)
        except:
            pass

    def load(self):
        try:
            with open(TASKS_FILE) as f:
                data = json.load(f)
            for tid, title in data.items():
                _tasks[Task(tid, title)] = title
        except:
            pass

    def format_task(self, task):
        return proc(task)
```

- [ ] **Step 6: Write `audit/corpus/tasklib/utils.py`**

Planted bugs: circular dep with manager (function-level import — detectable by AST but doesn't crash at import time), dead code, bad naming, unnecessary complexity.

```python
def proc(d):
    from tasklib.manager import TaskManager

    if isinstance(d, TaskManager):
        return f"TaskManager<{len(d.list_all())} tasks>"
    x = {
        k: str(v) for k, v in d.__dict__.items() if not k.startswith("_")
    } if hasattr(d, "__dict__") else {"v": str(d)}
    return " | ".join(f"{k}={v}" for k, v in x.items())


def _legacy_format(x):
    t = str(x)
    return t.upper()


def _unused_helper(t):
    d = list(range(len(str(t))))
    return [x * 2 for x in d]
```

- [ ] **Step 7: Write `audit/corpus/tasklib/__init__.py`**

Planted bug: re-exports `Config` which doesn't exist.

```python
from tasklib.models import Task, User
from tasklib.manager import TaskManager
from tasklib.db import get_connection

__all__ = ["Task", "User", "TaskManager", "get_connection", "Config"]
```

- [ ] **Step 8: Commit**

```bash
git add audit/corpus/tasklib/ audit/corpus/pyproject.toml
git commit -m "feat: add audit corpus Python source files"
```

---

### Task 2: Create corpus tests and documentation

**Files:**
- Create: `audit/corpus/tests/__init__.py`
- Create: `audit/corpus/tests/test_tasks.py`
- Create: `audit/corpus/README.md`
- Create: `audit/corpus/CHANGELOG.md`
- Create: `audit/corpus/docs/spec.md`
- Create: `audit/corpus/docs/plan.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p audit/corpus/tests audit/corpus/docs
```

- [ ] **Step 2: Write `audit/corpus/tests/__init__.py`**

Empty file:

```python
```

- [ ] **Step 3: Write `audit/corpus/tests/test_tasks.py`**

Planted bugs: over-mocking, vacuous assertions (`assert True`, `is not None`, `isinstance`), unfailable test, magic numbers, no edge cases.

```python
from unittest.mock import patch, MagicMock


def test_task_creation():
    assert True


@patch("tasklib.manager._tasks", {})
@patch("tasklib.db.get_connection")
@patch("tasklib.manager.open", create=True)
def test_add_task(mock_open, mock_conn):
    from tasklib.manager import TaskManager

    mgr = TaskManager()
    result = mgr.add("test task")
    assert result is not None


@patch("tasklib.manager._tasks", {})
@patch("tasklib.db.get_connection")
def test_list_tasks(mock_conn):
    from tasklib.manager import TaskManager

    mgr = TaskManager()
    mgr.add("a")
    mgr.add("b")
    mgr.add("c")
    result = mgr.list_all()
    assert len(result) == 3
    assert isinstance(result, list)


@patch("tasklib.manager._tasks", {})
def test_remove_task():
    from tasklib.manager import TaskManager

    mgr = TaskManager()
    mgr.add("to remove")
    mgr.remove(1)
    result = mgr.list_all()
    assert result is not None
```

- [ ] **Step 4: Write `audit/corpus/README.md`**

Every verifiable claim is wrong. Planted bugs: wrong install, phantom CLI, wrong API, false coverage/async claims.

Write the following content (note: backtick-fenced code blocks should use real triple backticks in the actual file):

- Title: "tasklib" with subtitle "A fully async task management library with 100% test coverage."
- Installation section: claims `pip install tasklib` (no setup.py/pyproject.toml with install config exists)
- Quick Start section: Python code block showing `manager.add("Buy groceries", priority="high")`, `manager.get_by_priority()`, and `manager.export_json("tasks.json")` — none of these APIs exist
- CLI section: bash code block showing `tasklib run --all`, `tasklib add "New task" --priority high`, `tasklib export output.json` — no CLI exists
- Features section: bullet list claiming "Async task operations", "Priority-based sorting", "JSON export/import", "Full CLI interface", "100% test coverage" — all false

- [ ] **Step 5: Write `audit/corpus/CHANGELOG.md`**

Planted bugs: phantom releases, false fix claims, missing entries, wrong dates.

```markdown
# Changelog

## v2.0.0 (2025-12-01)

- Complete async rewrite of all operations
- Added connection pooling for database layer
- Migrated to SQLAlchemy ORM

## v1.1.0 (2025-09-15)

- Fixed SQL injection vulnerability in db module
- Added input validation for task fields
- Improved error handling throughout

## v1.0.0 (2025-06-01)

- Initial release
- Basic CRUD operations
- SQLite storage backend
```

- [ ] **Step 6: Write `audit/corpus/docs/spec.md`**

5 features, only 2 partially implemented. Triggers spec_compliance_reviewer.

```markdown
# tasklib Feature Specification

## Overview

tasklib is a task management library supporting CRUD operations, tagging,
priority sorting, notifications, and data export.

## Features

### 1. CRUD Operations

Create, read, update, and delete tasks. Each task has an id, title, status,
and tags.

- `TaskManager.add(title, tags)` — create a new task
- `TaskManager.get(task_id)` — retrieve a task by id
- `TaskManager.remove(task_id)` — delete a task
- `TaskManager.list_all()` — list all tasks

### 2. Tagging System

Tasks support arbitrary string tags for categorization.

- Tags are passed at creation time
- Tags are stored as a list on each Task
- Support filtering by tag via `TaskManager.filter_by_tag(tag)`

### 3. Priority Sorting

Tasks have a priority field (high/medium/low) with sorting support.

- `Task.priority` field with validation
- `TaskManager.get_by_priority()` — returns tasks sorted by priority

### 4. Notifications

Email notifications when tasks are created or completed.

- `TaskManager.notify(task, event)` — send email notification
- Configurable SMTP settings

### 5. Export to JSON

Export all tasks to a JSON file.

- `TaskManager.export_json(path)` — write all tasks to file
- Include task id, title, tags, status, priority
```

- [ ] **Step 7: Write `audit/corpus/docs/plan.md`**

Small plan for the python_implementer agent.

```markdown
# Add JSON Export Feature

## Goal

Add `export_json(path)` method to TaskManager that writes all tasks to a
JSON file.

## Steps

1. Add `export_json(path: str)` method to `TaskManager` in `tasklib/manager.py`
   - Serialize all tasks from `_tasks` to a list of dicts
   - Each dict: `{"id": task_id, "title": title, "tags": tags, "done": done}`
   - Write to the given path using `json.dump`

2. Write tests for `export_json` in `tests/test_tasks.py`
   - Test export creates a valid JSON file
   - Test export with empty task list
   - Test export with multiple tasks

3. Update `README.md` with export documentation
```

- [ ] **Step 8: Commit**

```bash
git add audit/corpus/tests/ audit/corpus/README.md audit/corpus/CHANGELOG.md audit/corpus/docs/
git commit -m "feat: add audit corpus tests and documentation"
```

---

### Task 3: Write audit harness

**Files:**
- Create: `audit/run_audit.py`

- [ ] **Step 1: Write `audit/run_audit.py`**

Complete harness script. Key design decisions:
- Copies corpus to a tempdir with git initialized (isolation for write agents)
- Strips all agent hooks via `for_audit()` — audit tests agent logic, not CI checks
- Changes CWD to tempdir so git-dependent agents (changelog, readme reviewers) work
- Runs 3 phases: primary reviews (parallel) → downstream (sequential) → standalone (parallel)
- Saves one JSON per agent to `audit/results/<timestamp>/`

```python
"""Agent audit harness — runs all 11 codemonkeys agents against the test corpus."""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from codemonkeys.core.analysis import analyze_files, format_analysis
from codemonkeys.core.events import Event, EventCollector
from codemonkeys.core.runner import run_agent
from codemonkeys.core.types import AgentDefinition, RunResult

from codemonkeys.agents.architecture_reviewer import make_architecture_reviewer
from codemonkeys.agents.changelog_reviewer import make_changelog_reviewer
from codemonkeys.agents.fixer import make_fixer
from codemonkeys.agents.python_characterization_tester import (
    make_python_characterization_tester,
)
from codemonkeys.agents.python_implementer import make_python_implementer
from codemonkeys.agents.python_reviewer import make_python_reviewer
from codemonkeys.agents.python_structural_refactorer import (
    make_python_structural_refactorer,
)
from codemonkeys.agents.readme_reviewer import make_readme_reviewer
from codemonkeys.agents.review_auditor import auditor_from_result
from codemonkeys.agents.spec_compliance_reviewer import (
    PlanStep,
    make_spec_compliance_reviewer,
)
from codemonkeys.agents.triage import make_triage

CORPUS_DIR = Path(__file__).parent / "corpus"
RESULTS_DIR = Path(__file__).parent / "results"
SEM = asyncio.Semaphore(5)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def for_audit(agent: AgentDefinition) -> AgentDefinition:
    """Strip hooks for audit — test agent logic, not CI checks.

    Permission hooks (built from agent.tools) are preserved by the runner.
    Only PostToolUse / Stop / SubagentStart check-hooks are removed.
    """
    return replace(agent, hooks={})


def serialize_event(event: Event) -> dict[str, Any]:
    data: dict[str, Any] = {"type": type(event).__name__}
    for key, value in vars(event).items():
        if hasattr(value, "model_dump"):
            data[key] = value.model_dump()
        elif hasattr(value, "__dataclass_fields__"):
            data[key] = asdict(value)
        else:
            data[key] = value
    return data


def save_result(result: RunResult, name: str, output_dir: Path) -> None:
    data = {
        "agent_name": name,
        "model": result.agent_def.model if result.agent_def else "unknown",
        "output": result.output.model_dump() if result.output else None,
        "text": result.text,
        "events": [serialize_event(e) for e in result.events],
        "tokens": {
            "input": result.usage.input_tokens,
            "output": result.usage.output_tokens,
            "cache_read": result.usage.cache_read_tokens,
            "cache_creation": result.usage.cache_creation_tokens,
        },
        "cost_usd": result.cost_usd,
        "duration_seconds": result.duration_ms / 1000,
        "error": result.error,
    }
    (output_dir / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))


def save_summary(all_results: dict[str, RunResult], output_dir: Path) -> None:
    entries = []
    for name, result in all_results.items():
        entries.append(
            {
                "agent_name": name,
                "model": result.agent_def.model if result.agent_def else "unknown",
                "tokens_in": result.usage.input_tokens,
                "tokens_out": result.usage.output_tokens,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_ms / 1000,
                "success": result.error is None,
            }
        )
    (output_dir / "summary.json").write_text(json.dumps(entries, indent=2))


def print_summary_table(all_results: dict[str, RunResult]) -> None:
    table = Table(title="Audit Summary")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Tokens", justify="right")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Status", justify="center")
    total_cost = 0.0
    for name, result in all_results.items():
        tokens = result.usage.input_tokens + result.usage.output_tokens
        total_cost += result.cost_usd
        status = (
            "[green]OK[/green]"
            if result.error is None
            else "[red]ERR[/red]"
        )
        table.add_row(
            name,
            result.agent_def.model if result.agent_def else "?",
            f"{tokens:,}",
            f"${result.cost_usd:.4f}",
            f"{result.duration_ms / 1000:.1f}s",
            status,
        )
    console.print(table)
    console.print(f"\n[bold]Total cost: ${total_cost:.4f}[/bold]")


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


def setup_workspace() -> Path:
    """Copy corpus to tempdir and initialize git."""
    work_dir = Path(tempfile.mkdtemp(prefix="audit_corpus_"))
    shutil.copytree(CORPUS_DIR, work_dir, dirs_exist_ok=True)
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "audit",
        "GIT_AUTHOR_EMAIL": "audit@test.com",
        "GIT_COMMITTER_NAME": "audit",
        "GIT_COMMITTER_EMAIL": "audit@test.com",
    }
    subprocess.run(
        ["git", "init"], cwd=work_dir, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "add", "."], cwd=work_dir, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=work_dir,
        capture_output=True,
        check=True,
        env=git_env,
    )
    return work_dir


async def run_one(agent: AgentDefinition, prompt: str) -> RunResult:
    """Run a single agent with event collection."""
    async with SEM:
        collector = EventCollector()
        console.print(f"  [dim]Starting {agent.name}...[/dim]")
        result = await run_agent(agent, prompt, on_event=collector.handle)
        result.events = collector.events
        status = (
            "[green]OK[/green]" if result.error is None else "[red]ERR[/red]"
        )
        console.print(
            f"  {agent.name} {status}"
            f" ({result.duration_ms / 1000:.1f}s, ${result.cost_usd:.4f})"
        )
        return result


async def run_parallel(
    agents: dict[str, tuple[AgentDefinition, str]],
) -> dict[str, RunResult]:
    """Run multiple agents in parallel, collecting results by name."""
    names = list(agents.keys())
    coros = [run_one(agent, prompt) for agent, prompt in agents.values()]
    gathered = await asyncio.gather(*coros, return_exceptions=True)
    results: dict[str, RunResult] = {}
    for name, result in zip(names, gathered):
        if isinstance(result, Exception):
            console.print(f"  [red]{name} failed: {result}[/red]")
        else:
            results[name] = result
    return results


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------


async def phase1(work_dir: Path) -> dict[str, RunResult]:
    """Primary reviews — python reviewer, architecture, readme, changelog."""
    console.print("\n[bold blue]Phase 1: Primary Reviews[/bold blue]")

    src_files = [
        str(work_dir / "tasklib" / f)
        for f in ("models.py", "manager.py", "db.py", "utils.py")
    ]
    test_files = [str(work_dir / "tests" / "test_tasks.py")]
    all_py = src_files + test_files

    # Architecture reviewer needs structural metadata
    analyses = analyze_files(src_files, root=work_dir)
    structural_metadata = format_analysis(analyses)
    file_summaries = [
        {"file": str(work_dir / "tasklib" / "models.py"),
         "summary": "Data models for Task and User entities"},
        {"file": str(work_dir / "tasklib" / "manager.py"),
         "summary": "TaskManager class — CRUD, persistence, and formatting"},
        {"file": str(work_dir / "tasklib" / "db.py"),
         "summary": "SQLite database operations for task storage"},
        {"file": str(work_dir / "tasklib" / "utils.py"),
         "summary": "Utility functions for formatting and data processing"},
    ]

    agents: dict[str, tuple[AgentDefinition, str]] = {}

    # Python reviewer — batch files in groups of 3
    batches = [all_py[:3], all_py[3:]]
    for i, batch in enumerate(batches):
        agents[f"python_reviewer_batch{i}"] = (
            for_audit(make_python_reviewer(batch)),
            "Review the listed files.",
        )

    agents["architecture_reviewer"] = (
        for_audit(
            make_architecture_reviewer(
                files=src_files,
                file_summaries=file_summaries,
                structural_metadata=structural_metadata,
            )
        ),
        "Review the architecture of this codebase.",
    )

    agents["readme_reviewer"] = (
        for_audit(make_readme_reviewer()),
        f"Review the project README at {work_dir / 'README.md'}."
        f" The project root is {work_dir}.",
    )

    agents["changelog_reviewer"] = (
        for_audit(make_changelog_reviewer()),
        f"Review the project CHANGELOG at {work_dir / 'CHANGELOG.md'}."
        f" The project root is {work_dir}.",
    )

    return await run_parallel(agents)


async def phase2(
    phase1_results: dict[str, RunResult],
    work_dir: Path,
) -> dict[str, RunResult]:
    """Downstream agents — auditor, triage, fixer (sequential)."""
    console.print("\n[bold blue]Phase 2: Downstream Agents[/bold blue]")
    results: dict[str, RunResult] = {}

    # Review auditor — audit each python_reviewer result
    for name, result in phase1_results.items():
        if not name.startswith("python_reviewer") or result.error:
            continue
        auditor = for_audit(auditor_from_result(result))
        audit_name = name.replace("python_reviewer", "review_auditor")
        results[audit_name] = await run_one(auditor, "Audit this review.")

    # Collect all findings from python reviewers
    all_findings = []
    for name, result in phase1_results.items():
        if name.startswith("python_reviewer") and result.output:
            all_findings.extend(result.output.results)

    if not all_findings:
        console.print("  [yellow]No findings — skipping triage and fixer[/yellow]")
        return results

    # Triage — auto-select high severity (no interactive prompt)
    triage_agent = for_audit(make_triage(all_findings))
    triage_result = await run_one(
        triage_agent, "Select all high severity findings."
    )
    results["triage"] = triage_result

    # Fixer — apply triaged findings
    if triage_result.output and triage_result.output.selected:
        selected = [
            all_findings[i - 1]
            for i in triage_result.output.selected
            if 1 <= i <= len(all_findings)
        ]
        if selected:
            fixer_agent = for_audit(make_fixer(selected))
            results["fixer"] = await run_one(
                fixer_agent,
                "Apply the fixes described in your system prompt.",
            )

    return results


async def phase3(work_dir: Path) -> dict[str, RunResult]:
    """Standalone agents — refactorer, tester, compliance, implementer."""
    console.print("\n[bold blue]Phase 3: Standalone Agents[/bold blue]")

    src_files = [
        str(work_dir / "tasklib" / f)
        for f in ("models.py", "manager.py", "db.py", "utils.py")
    ]
    test_files = [str(work_dir / "tests" / "test_tasks.py")]

    # Structural metadata for characterization tester
    analyses = analyze_files(src_files, root=work_dir)
    import_context = format_analysis(analyses)

    # Spec steps for compliance reviewer
    spec_steps = [
        PlanStep(
            description="CRUD operations: add, get, remove, list_all",
            files=["tasklib/manager.py"],
        ),
        PlanStep(
            description="Tagging system: tags on tasks, filter_by_tag",
            files=["tasklib/models.py", "tasklib/manager.py"],
        ),
        PlanStep(
            description="Priority sorting: priority field, get_by_priority",
            files=["tasklib/models.py", "tasklib/manager.py"],
        ),
        PlanStep(
            description="Email notifications: notify on create/complete",
            files=["tasklib/manager.py"],
        ),
        PlanStep(
            description="Export to JSON: export_json method",
            files=["tasklib/manager.py"],
        ),
    ]

    plan_text = (work_dir / "docs" / "plan.md").read_text()

    agents: dict[str, tuple[AgentDefinition, str]] = {}

    agents["structural_refactorer_god"] = (
        for_audit(
            make_python_structural_refactorer(
                files=[str(work_dir / "tasklib" / "manager.py")],
                problem_description=(
                    "TaskManager is a god module handling CRUD, validation,"
                    " notification, formatting, and file I/O persistence."
                    " Split responsibilities into focused modules."
                ),
                refactor_type="god_modules",
                test_files=test_files,
            )
        ),
        "Refactor the god module as described.",
    )

    agents["structural_refactorer_circular"] = (
        for_audit(
            make_python_structural_refactorer(
                files=[
                    str(work_dir / "tasklib" / "manager.py"),
                    str(work_dir / "tasklib" / "utils.py"),
                ],
                problem_description=(
                    "manager.py imports from utils.py and utils.py imports"
                    " from manager.py, creating a circular dependency."
                ),
                refactor_type="circular_deps",
                test_files=test_files,
            )
        ),
        "Resolve the circular dependency as described.",
    )

    agents["characterization_tester"] = (
        for_audit(
            make_python_characterization_tester(
                files=src_files,
                import_context=import_context,
            )
        ),
        "Write characterization tests for the listed modules.",
    )

    agents["spec_compliance_reviewer"] = (
        for_audit(
            make_spec_compliance_reviewer(
                spec_title="tasklib Feature Specification",
                spec_description=(
                    "Task management library with CRUD, tagging, priority"
                    " sorting, notifications, and JSON export."
                ),
                steps=spec_steps,
                files=src_files + test_files,
                unplanned_files=[],
            )
        ),
        "Check implementation against the specification.",
    )

    agents["python_implementer"] = (
        for_audit(make_python_implementer()),
        plan_text,
    )

    return await run_parallel(agents)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    console.print("[bold]Setting up audit workspace...[/bold]")
    work_dir = setup_workspace()
    console.print(f"[dim]Workspace: {work_dir}[/dim]")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    output_dir = RESULTS_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_cwd = os.getcwd()
    os.chdir(work_dir)
    try:
        all_results: dict[str, RunResult] = {}
        p1 = await phase1(work_dir)
        all_results.update(p1)
        p2 = await phase2(p1, work_dir)
        all_results.update(p2)
        p3 = await phase3(work_dir)
        all_results.update(p3)
    finally:
        os.chdir(saved_cwd)

    console.print("\n[bold]Saving results...[/bold]")
    for name, result in all_results.items():
        save_result(result, name, output_dir)
    save_summary(all_results, output_dir)
    print_summary_table(all_results)

    shutil.rmtree(work_dir)
    console.print(f"\n[bold green]Results saved to {output_dir}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify imports resolve**

Run from the project root:

```bash
uv run python -c "from audit.run_audit import main; print('imports OK')"
```

Expected: `imports OK` (or import errors that need fixing — adjust imports to match actual module paths).

- [ ] **Step 3: Commit**

```bash
git add audit/run_audit.py
git commit -m "feat: add audit harness script"
```

---

### Task 4: Smoke test

- [ ] **Step 1: Run the audit**

```bash
uv run python -m audit.run_audit
```

Expected: the harness sets up a workspace, runs all 11 agents across 3 phases, prints a summary table, and saves JSON results to `audit/results/<timestamp>/`.

This will make real API calls and cost money. Expect $2-5 depending on agent token usage. The run takes 5-15 minutes depending on API latency.

- [ ] **Step 2: Check results directory**

```bash
ls audit/results/
```

Expected: a timestamped directory containing one JSON file per agent plus `summary.json`.

- [ ] **Step 3: Spot-check a reviewer result**

```bash
cat audit/results/*/python_reviewer_batch0.json | python -m json.tool | head -30
```

Expected: JSON with `agent_name`, `model`, `output` (containing findings), `tokens`, `cost_usd`, `duration_seconds`.

- [ ] **Step 4: Commit results gitignore**

Add `audit/results/` to `.gitignore` so result data isn't committed:

```bash
echo "audit/results/" >> .gitignore
git add .gitignore
git commit -m "chore: gitignore audit results"
```
