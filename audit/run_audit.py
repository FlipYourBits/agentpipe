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
from codemonkeys.core.events import Event
from codemonkeys.core.runner import run_agent
from codemonkeys.core.types import AgentDefinition, RunResult, TokenUsage

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
        console.print(f"  [dim]Starting {agent.name}...[/dim]")
        result = await run_agent(agent, prompt)
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
            agent_def = agents[name][0]
            results[name] = RunResult(
                output=None,
                text="",
                usage=TokenUsage(input_tokens=0, output_tokens=0),
                cost_usd=0.0,
                duration_ms=0,
                error=str(result),
                agent_def=agent_def,
                events=[],
            )
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
    batches = [b for b in [all_py[:3], all_py[3:]] if b]
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
        shutil.rmtree(work_dir, ignore_errors=True)

    console.print("\n[bold]Saving results...[/bold]")
    for name, result in all_results.items():
        save_result(result, name, output_dir)
    save_summary(all_results, output_dir)
    print_summary_table(all_results)

    console.print(f"\n[bold green]Results saved to {output_dir}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
