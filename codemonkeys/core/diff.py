"""Capture before/after diffs of agent file changes."""

from __future__ import annotations

import subprocess
from pathlib import Path


def snapshot() -> str:
    """Bookmark the current working tree state without modifying it.

    Returns a git ref suitable for diffing against later.
    """
    result = subprocess.run(
        ["git", "stash", "create"],
        capture_output=True, text=True, check=True,
    )
    ref = result.stdout.strip()
    return ref if ref else "HEAD"


def generate_patch(
    base_ref: str,
    new_files: list[str],
    patch_path: Path,
) -> Path | None:
    """Generate a unified diff between *base_ref* and the current working tree.

    Tracked-file changes come from ``git diff``.  Brand-new files (not yet
    in the index) are diffed individually against ``/dev/null`` so they
    appear as additions in the patch.

    Returns the written path, or ``None`` if nothing changed.
    """
    tracked = subprocess.run(
        ["git", "diff", base_ref],
        capture_output=True, text=True,
    ).stdout

    new_diffs: list[str] = []
    for f in new_files:
        if not Path(f).exists():
            continue
        r = subprocess.run(
            ["git", "diff", "--no-index", "/dev/null", f],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            new_diffs.append(r.stdout)

    combined = tracked + "\n".join(new_diffs)
    if not combined.strip():
        return None

    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(combined)
    return patch_path


def print_patch(patch_path: Path, console: "Console | None" = None) -> None:
    """Print a patch file to the console with diff syntax highlighting."""
    from rich.console import Console
    from rich.syntax import Syntax

    con = console or Console(stderr=True)
    content = patch_path.read_text()
    con.print()
    con.rule("Changes", style="dim")
    con.print(Syntax(content, "diff", theme="monokai"))
    con.print(f"\n[dim]Patch saved: {patch_path}[/dim]")
