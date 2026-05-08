"""Review workflow — discover files, review, triage findings, fix.

Usage:
    uv run python -m codemonkeys.workflows.review
    uv run python -m codemonkeys.workflows.review 'codemonkeys/core/**/*.py'
    uv run python -m codemonkeys.workflows.review '**/*.py' --audit
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from codemonkeys.agents.fixer import make_fixer
from codemonkeys.agents.python_reviewer import make_python_reviewer
from codemonkeys.agents.review_auditor import auditor_from_result
from codemonkeys.agents.triage import run_triage
from codemonkeys.core.discovery import batch, discover_files
from codemonkeys.core.runner import run_agent
from codemonkeys.core.events import EventHandler
from codemonkeys.core.types import AgentDefinition, RunResult, make_log_dir
from codemonkeys.display.logger import FileLogger
from codemonkeys.display.results import (
    print_audit_summary,
    print_fix_result,
    print_review_summary,
    save_outputs,
)
from codemonkeys.display.stdout import fan_out, make_stdout_printer

_printer = make_stdout_printer()


@contextmanager
def _logged(log_dir: Path, name: str) -> Iterator[EventHandler]:
    logger = FileLogger(log_dir / f"{name}.jsonl")
    try:
        yield fan_out(_printer, logger.handle)
    finally:
        logger.close()


_MAX_CONCURRENT = 5


async def _run_parallel(
    agents: list[AgentDefinition], prompt: str, on_event: EventHandler,
) -> list[RunResult]:
    sem = asyncio.Semaphore(_MAX_CONCURRENT)

    async def _limited(agent: AgentDefinition) -> RunResult:
        async with sem:
            return await run_agent(agent, prompt, on_event=on_event)

    return list(await asyncio.gather(*[_limited(a) for a in agents]))


async def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    pattern = positional[0] if positional else "**/*.py"
    audit = "--audit" in sys.argv

    files = discover_files(pattern)
    if not files:
        print(f"No files found matching '{pattern}'")
        return

    batches = batch(files)
    print(f"\n{len(files)} file(s) in {len(batches)} batch(es):\n")
    for f in files:
        print(f"  {f}")
    print()

    log_dir = make_log_dir("review")

    # Review
    with _logged(log_dir, "review") as on_event:
        reviewers = [make_python_reviewer(b) for b in batches]
        results = await _run_parallel(reviewers, "Review the listed files.", on_event)

    save_outputs(results, log_dir)
    all_findings = print_review_summary(results)

    # Audit (optional)
    if audit:
        successful = [r for r in results if not r.error and r.agent_def]
        if successful:
            with _logged(log_dir, "audit") as on_event:
                auditors = [auditor_from_result(r) for r in successful]
                audit_results = await _run_parallel(auditors, "Audit this review.", on_event)

            save_outputs(audit_results, log_dir)
            print_audit_summary([
                (r.agent_def.name if r.agent_def else "?", ar)
                for r, ar in zip(successful, audit_results)
            ])

    if not all_findings:
        return

    # Triage
    with _logged(log_dir, "triage") as on_event:
        selected = await run_triage(all_findings, on_event=on_event)

    if not selected:
        return

    # Fix
    with _logged(log_dir, "fix") as on_event:
        fix_result = await run_agent(
            make_fixer(selected), "Apply the fixes described in your system prompt.", on_event=on_event,
        )

    print_fix_result(fix_result)


if __name__ == "__main__":
    asyncio.run(main())
