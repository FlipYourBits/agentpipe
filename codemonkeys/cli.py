"""CLI entry point for codemonkeys agent pipelines."""

from __future__ import annotations

import argparse
import asyncio
import fnmatch
import importlib.resources
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console

from codemonkeys.agents import get_reviewer
from codemonkeys.core.discovery import discover_files
from codemonkeys.core.runner import run_agent
from codemonkeys.core.types import (
    AgentDefinition,
    AuditFinding,
    AuditResults,
    FileReviewResult,
    RunResult,
    make_log_dir,
)
from codemonkeys.display.file_printer import make_file_printer
from codemonkeys.display.logger import load_run_meta, logged, save_run_meta
from codemonkeys.display.stdout import fan_out, make_stdout_printer

_console = Console(stderr=True)

DEFAULT_MAX_PARALLEL = 4


def _get_diff_files() -> list[str]:
    """Get files changed on the current branch vs the default remote branch."""
    base = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
    )
    default_branch = (
        base.stdout.strip().rsplit("/", 1)[-1] if base.returncode == 0 else "main"
    )
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{default_branch}...HEAD"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


def _add_editor_args(parser: argparse.ArgumentParser) -> None:
    """Add shared arguments for edit and implement subcommands."""
    parser.add_argument("file_paths", nargs="+", help="File(s) to edit")
    parser.add_argument(
        "--task", type=str, default=None, help="Task description (inline)",
    )
    parser.add_argument(
        "--task-file", type=str, default=None, help="Read task description from a file",
    )
    parser.add_argument(
        "--read-paths", type=str, default=None,
        help="Comma-separated extra files the agent can read for context",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codemonkeys",
        description="Code review and editing agents.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- review (read-only) ---
    review = sub.add_parser(
        "review", help="Review files for issues (read-only)",
    )
    review.add_argument(
        "patterns", nargs="*",
        help="Glob patterns (e.g. '**/*.py', 'src/**/*.js')",
    )
    review.add_argument(
        "--diff", action="store_true",
        help="Only review files changed on the current branch",
    )
    review.add_argument(
        "--max-parallel", type=int, default=None,
        help=f"Max concurrent agents (default: {DEFAULT_MAX_PARALLEL})",
    )
    review.add_argument(
        "--quiet", action="store_true",
        help="Suppress live output (auto-enabled when not a TTY)",
    )

    # --- edit (fix, refactor existing files) ---
    edit = sub.add_parser(
        "edit", help="Edit existing files — fix bugs, apply findings, refactor",
    )
    _add_editor_args(edit)
    edit.add_argument(
        "--task-type", type=str, default="fix",
        help="Task type: fix, refactor (default: fix)",
    )
    edit.add_argument(
        "--findings", type=str, default=None,
        help="Comma-separated finding indices from review-results.json (1-based)",
    )
    edit.add_argument(
        "--results", type=str, default=".codemonkeys/review-results.json",
        help="Path to review results JSON (used with --findings)",
    )

    # --- implement (create new files, build features) ---
    implement = sub.add_parser(
        "implement", help="Implement features — create files, write tests, add docs",
    )
    _add_editor_args(implement)
    implement.add_argument(
        "--task-type", type=str, default="feat",
        help="Task type: feat, test, docs (default: feat)",
    )

    # --- init ---
    init = sub.add_parser(
        "init", help="Install Claude Code skills into the current project",
    )
    init.add_argument(
        "--force", action="store_true", help="Overwrite existing skill files",
    )

    return parser


def _find_skills_root() -> Path:
    """Locate the skills directory — packaged wheel or development source."""
    pkg = importlib.resources.files("codemonkeys") / "skills"
    pkg_path = Path(str(pkg))
    if pkg_path.is_dir():
        return pkg_path
    repo_root = Path(__file__).resolve().parent.parent
    dev_path = repo_root / ".claude" / "skills"
    if dev_path.is_dir():
        return dev_path
    return pkg_path


def _run_init(force: bool = False) -> None:
    skills_root = _find_skills_root()
    dest = Path(".claude") / "skills"
    dest.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []

    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue

        target_dir = dest / skill_dir.name
        target_file = target_dir / "SKILL.md"

        if target_file.exists() and not force:
            skipped.append(skill_dir.name)
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(skill_file.read_text())
        installed.append(skill_dir.name)

    if installed:
        _console.print(f"[bold]Installed {len(installed)} skill(s):[/bold]")
        for name in installed:
            _console.print(f"  [green]+[/green] {name}")

    if skipped:
        _console.print(f"\n[yellow]Skipped {len(skipped)} existing skill(s) (use --force to overwrite):[/yellow]")
        for name in skipped:
            _console.print(f"  [dim]-[/dim] {name}")

    if not installed and not skipped:
        _console.print("[yellow]No skills found in package.[/yellow]")


def _resolve_max_parallel(cli_value: int | None) -> int:
    if cli_value is not None:
        return cli_value
    return int(os.environ.get("CODEMONKEYS_MAX_PARALLEL_AGENTS", DEFAULT_MAX_PARALLEL))


# ---------------------------------------------------------------------------
# review (read-only)
# ---------------------------------------------------------------------------


async def _run_review(
    files: list[str],
    max_parallel: int,
    quiet: bool,
) -> None:
    log_dir = make_log_dir("review")
    use_stdout = not quiet and sys.stdout.isatty()
    sem = asyncio.Semaphore(max_parallel)
    total = len(files)
    done_count = 0
    all_findings: list[AuditFinding] = []

    async def _review_one(file_path: str) -> RunResult | BaseException:
        nonlocal done_count
        async with sem:
            ext = Path(file_path).suffix
            factory = get_reviewer(ext)
            assert factory is not None, f"No reviewer for {ext} — should have been filtered"
            agent = factory(file_path)
            prompt = f"Read `{file_path}` and review it. Report any issues you find."
            log_name = re.sub(r"[^\w\-.]", "_", f"reviewer_{file_path}")
            save_run_meta(log_dir, log_name, agent, prompt)
            file_log = make_file_printer(log_dir / f"{log_name}.log")
            if use_stdout:
                stdout_printer = make_stdout_printer()
                printer = fan_out(stdout_printer, file_log)
            else:
                printer = file_log
            with logged(log_dir, log_name, printer=printer) as evt:
                result = await run_agent(agent, prompt, on_event=evt, log_dir=log_dir)
        done_count += 1

        findings_count = 0
        if isinstance(result.output, FileReviewResult):
            all_findings.extend(result.output.findings)
            findings_count = len(result.output.findings)

        status = "[red]FAIL[/red]" if result.error else "[green]OK[/green]"
        _console.print(f"  {status} {file_path} — {findings_count} finding(s) ({done_count}/{total})")
        return result

    _console.print(f"[bold]Reviewing {total} file(s) (max {max_parallel} parallel)[/bold]\n")

    raw_results = await asyncio.gather(
        *[_review_one(f) for f in files], return_exceptions=True
    )

    results = [r for r in raw_results if isinstance(r, RunResult)]
    errors = [r for r in results if r.error]
    crashes = [r for r in raw_results if isinstance(r, BaseException)]
    total_cost = sum(r.cost_usd for r in results)

    review_results = AuditResults(files_reviewed=files, findings=all_findings)
    results_path = Path(".codemonkeys") / "review-results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(review_results.model_dump_json(indent=2))

    _console.print()
    _console.print(
        f"[bold]Done.[/bold] {total} files reviewed, "
        f"{len(all_findings)} finding(s), {len(errors)} errors, {len(crashes)} crashed"
    )
    _console.print(f"[dim]Total cost: ${total_cost:.4f}[/dim]")
    _console.print(f"[dim]Results: {results_path}[/dim]")
    _console.print(f"[dim]Logs: {log_dir}[/dim]")


# ---------------------------------------------------------------------------
# edit / implement (shared runner)
# ---------------------------------------------------------------------------


def _task_from_findings(
    file_path: str, finding_indices: list[int] | None, results_path: str,
) -> str | None:
    """Build a task description from review findings. Returns None if no findings."""
    rp = Path(results_path)
    if not rp.exists():
        _console.print(f"[red]Results file not found: {rp}[/red]")
        raise SystemExit(1)

    audit_results = AuditResults.model_validate_json(rp.read_text())
    file_findings = [f for f in audit_results.findings if f.file == file_path]

    if not file_findings:
        _console.print(f"[yellow]No findings for {file_path}[/yellow]")
        return None

    if finding_indices:
        selected = []
        for i in finding_indices:
            if 1 <= i <= len(file_findings):
                selected.append(file_findings[i - 1])
            else:
                _console.print(f"[yellow]Finding index {i} out of range (1-{len(file_findings)})[/yellow]")
        file_findings = selected

    if not file_findings:
        _console.print("[yellow]No valid findings selected.[/yellow]")
        return None

    task_lines = [f"Fix the following {len(file_findings)} issue(s) in `{file_path}`:\n"]
    for i, f in enumerate(file_findings, 1):
        task_lines.append(f"### {i}. [{f.severity}] {f.title}")
        if f.line:
            task_lines.append(f"Line: {f.line}")
        task_lines.append(f"Category: {f.category}")
        task_lines.append(f"{f.description}")
        if f.suggestion:
            task_lines.append(f"Suggested fix: {f.suggestion}")
        task_lines.append("")

    return "\n".join(task_lines)


async def _run_editor(
    file_paths: list[str],
    task: str,
    task_type: str,
    read_paths: list[str] | None,
) -> None:
    from codemonkeys.agents.code_editor import make_code_editor
    agent = make_code_editor(
        file_paths if len(file_paths) > 1 else file_paths[0],
        task=task, task_type=task_type, read_paths=read_paths,
    )
    log_dir = make_log_dir(task_type)
    slug = file_paths[0] if len(file_paths) == 1 else f"{len(file_paths)}_files"
    log_name = re.sub(r"[^\w\-.]", "_", f"{task_type}_{slug}")
    save_run_meta(log_dir, log_name, agent, task)
    file_log = make_file_printer(log_dir / f"{log_name}.log")
    if sys.stdout.isatty():
        printer = fan_out(make_stdout_printer(), file_log)
    else:
        printer = file_log

    files_label = ", ".join(file_paths) if len(file_paths) <= 3 else f"{len(file_paths)} files"
    _console.print(f"[bold]Running {task_type} on {files_label}[/bold]\n")

    with logged(log_dir, log_name, printer=printer) as evt:
        result = await run_agent(agent, task, on_event=evt, log_dir=log_dir)

    status = "[red]FAIL[/red]" if result.error else "[green]OK[/green]"
    _console.print(f"\n  {status} {files_label}")
    _console.print(f"[dim]Cost: ${result.cost_usd:.4f}[/dim]")
    _console.print(f"[dim]Logs: {log_dir}[/dim]")
    diff_paths = " ".join(file_paths)
    _console.print(f"[dim]Review changes: git diff {diff_paths}[/dim]")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _resolve_task(args: argparse.Namespace) -> str:
    """Resolve task description from --task, --task-file, or --findings."""
    task: str | None = args.task
    if args.task_file:
        tf = Path(args.task_file)
        if not tf.exists():
            _console.print(f"[red]Task file not found: {tf}[/red]")
            raise SystemExit(1)
        task = tf.read_text()
    if not task and hasattr(args, "findings") and args.findings:
        indices = [int(x.strip()) for x in args.findings.split(",")]
        task = _task_from_findings(args.file_paths[0], indices, args.results)
    if not task:
        _console.print("[red]Provide --task, --task-file, or --findings[/red]")
        raise SystemExit(1)
    return task


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        raise SystemExit(1)

    if args.command == "review":
        if args.diff:
            all_files = _get_diff_files()
            if args.patterns:
                filtered = []
                for f in all_files:
                    if any(fnmatch.fnmatch(f, p) for p in args.patterns):
                        filtered.append(f)
                all_files = filtered
        elif args.patterns:
            all_files = []
            for pat in args.patterns:
                all_files.extend(discover_files(pat))
            all_files = sorted(set(all_files))
        else:
            _console.print("[red]Provide glob patterns or use --diff[/red]")
            raise SystemExit(1)

        if not all_files:
            _console.print("[yellow]No files found.[/yellow]")
            raise SystemExit(0)

        by_ext: dict[str, list[str]] = defaultdict(list)
        for f in all_files:
            by_ext[Path(f).suffix].append(f)

        reviewable: list[str] = []
        for ext, ext_files in sorted(by_ext.items()):
            if get_reviewer(ext) is not None:
                reviewable.extend(ext_files)
            else:
                _console.print(
                    f"[yellow]No reviewer for {ext} files, skipping {len(ext_files)} file(s)[/yellow]"
                )

        if not reviewable:
            _console.print("[yellow]No reviewable files found.[/yellow]")
            raise SystemExit(0)

        max_parallel = _resolve_max_parallel(args.max_parallel)
        quiet = args.quiet or not sys.stdout.isatty()
        asyncio.run(_run_review(reviewable, max_parallel, quiet=quiet))

    elif args.command in ("edit", "implement"):
        task = _resolve_task(args)
        read_paths = None
        if args.read_paths:
            read_paths = [p.strip() for p in args.read_paths.split(",")]
        asyncio.run(_run_editor(args.file_paths, task, args.task_type, read_paths))

    elif args.command == "init":
        _run_init(force=args.force)

