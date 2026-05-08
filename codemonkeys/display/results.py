"""Rich summary tables for review and fix results."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from codemonkeys.agents.fixer import FixResult
from codemonkeys.agents.python_reviewer import FileFindings, Finding
from codemonkeys.agents.review_auditor import ReviewAudit
from codemonkeys.core.types import RunResult
from codemonkeys.display.formatting import severity_style

console = Console()

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def print_review_summary(results: list[RunResult]) -> list[Finding]:
    all_findings: list[Finding] = []
    total_cost = 0.0
    for r in results:
        total_cost += r.cost_usd
        if r.error:
            console.print(f"[red]Agent error: {r.error}[/red]")
            continue
        if isinstance(r.output, FileFindings):
            all_findings.extend(r.output.results)

    if not all_findings:
        console.print("\n[green]No findings.[/green]")
        return all_findings

    high = sum(1 for f in all_findings if f.severity.lower() == "high")
    medium = sum(1 for f in all_findings if f.severity.lower() == "medium")
    low = sum(1 for f in all_findings if f.severity.lower() == "low")

    console.print()
    console.rule(
        f"[bold]{len(all_findings)} findings[/bold] "
        f"([red]{high} high[/red], [yellow]{medium} medium[/yellow], [blue]{low} low[/blue]) "
        f"| Cost: ${total_cost:.4f}",
        style="dim",
    )

    by_file: dict[str, list[Finding]] = {}
    for f in all_findings:
        by_file.setdefault(f.file, []).append(f)

    for file_path, findings in sorted(by_file.items()):
        table = Table(
            title=file_path, title_style="bold",
            show_lines=True, expand=True, highlight=False,
        )
        table.add_column("Sev", width=6, justify="center", no_wrap=True)
        table.add_column("Line", width=6, justify="right", no_wrap=True)
        table.add_column("Issue", ratio=3)
        table.add_column("Suggestion", ratio=2)

        for finding in sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity.lower(), 9), f.line or 0),
        ):
            style = severity_style(finding.severity)
            sev = f"[{style}]{finding.severity.upper()}[/{style}]"
            line_ref = str(finding.line) if finding.line else ""
            issue = f"[bold]{escape(finding.title)}[/bold]"
            if finding.description:
                issue += f"\n{escape(finding.description)}"
            suggestion = escape(finding.suggestion) if finding.suggestion else ""
            table.add_row(sev, line_ref, issue, suggestion)

        console.print()
        console.print(table)

    return all_findings


def print_audit_summary(audit_results: list[tuple[str, RunResult]]) -> None:
    verdicts: list[str] = []
    total_cost = 0.0
    for _, r in audit_results:
        total_cost += r.cost_usd
        if isinstance(r.output, ReviewAudit):
            verdicts.append(r.output.verdict.lower())

    passes = verdicts.count("pass")
    warns = verdicts.count("warn")
    fails = verdicts.count("fail")

    console.print()
    console.rule(
        f"[bold]AUDIT[/bold] — "
        f"[bold]{len(audit_results)} audit(s)[/bold] "
        f"([green]{passes} pass[/green], [yellow]{warns} warn[/yellow], "
        f"[red]{fails} fail[/red]) "
        f"| Cost: ${total_cost:.4f}",
        style="magenta",
    )

    for reviewer_name, result in audit_results:
        if result.error:
            console.print(f"\n  [red]{reviewer_name} — audit error: {result.error}[/red]")
            continue
        if not isinstance(result.output, ReviewAudit):
            console.print(f"\n  [yellow]{reviewer_name} — no structured audit output[/yellow]")
            continue

        audit = result.output
        vstyle = {"pass": "bold green", "warn": "bold yellow", "fail": "bold red"}.get(
            audit.verdict.lower(), "white"
        )

        table = Table(
            title=f"{reviewer_name} — [{vstyle}]{audit.verdict.upper()}[/{vstyle}]",
            title_style="bold", caption=audit.summary, caption_style="dim",
            show_lines=True, expand=True, highlight=False,
        )
        table.add_column("Sev", width=6, justify="center", no_wrap=True)
        table.add_column("Category", width=14, no_wrap=True)
        table.add_column("Finding", ratio=3)
        table.add_column("Suggestion", ratio=2)

        if audit.results:
            for f in sorted(
                audit.results,
                key=lambda f: SEVERITY_ORDER.get(f.severity.lower(), 9),
            ):
                sev_style = severity_style(f.severity)
                sev = f"[{sev_style}]{f.severity.upper()}[/{sev_style}]"
                finding_text = f"[bold]{escape(f.title)}[/bold]"
                if f.description:
                    finding_text += f"\n{escape(f.description)}"
                suggestion = escape(f.suggestion) if f.suggestion else ""
                table.add_row(sev, f.category, finding_text, suggestion)
        else:
            table.add_row("[green]--[/green]", "--", "[green]No issues found[/green]", "")

        console.print()
        console.print(table)


def print_fix_result(result: RunResult) -> None:
    if result.error:
        console.print(f"\n[red]Fixer error: {result.error}[/red]")
        return
    if not isinstance(result.output, FixResult):
        console.print("\n[yellow]No structured result from fixer.[/yellow]")
        return

    fix = result.output
    console.print()
    if fix.applied:
        console.print(f"[green]Applied ({len(fix.applied)}):[/green]")
        for title in fix.applied:
            console.print(f"  [green]+[/green] {escape(title)}")
    if fix.skipped:
        console.print(f"[yellow]Skipped ({len(fix.skipped)}):[/yellow]")
        for reason in fix.skipped:
            console.print(f"  [yellow]-[/yellow] {escape(reason)}")
    console.print(f"\n[dim]{fix.summary}[/dim]")


def print_findings_table(items: list) -> None:
    """Print a numbered table of FixItems for interactive selection."""
    table = Table(
        title="Findings", title_style="bold",
        show_lines=True, expand=True, highlight=False,
    )
    table.add_column("#", width=4, justify="right", no_wrap=True)
    table.add_column("Sev", width=6, justify="center", no_wrap=True)
    table.add_column("Location", width=30, no_wrap=True)
    table.add_column("Issue", ratio=3)
    table.add_column("Suggestion", ratio=2)

    sorted_items = sorted(
        enumerate(items, 1),
        key=lambda x: SEVERITY_ORDER.get((x[1].severity or "").lower(), 9),
    )

    for idx, item in sorted_items:
        sev = ""
        if item.severity:
            style = severity_style(item.severity)
            sev = f"[{style}]{item.severity.upper()}[/{style}]"

        loc = ""
        if item.file:
            loc = escape(item.file)
            if item.line:
                loc += f":{item.line}"

        issue = f"[bold]{escape(item.title)}[/bold]"
        if item.description and item.description != item.title:
            issue += f"\n{escape(item.description)}"

        suggestion = escape(item.suggestion) if item.suggestion else ""
        table.add_row(str(idx), sev, loc, issue, suggestion)

    console.print(table)


def save_outputs(results: list[RunResult], log_dir: Path) -> None:
    for result in results:
        path = result.save_output(log_dir)
        if path:
            console.print(f"  [dim]{path}[/dim]")
