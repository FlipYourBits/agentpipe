"""File discovery via git ls-files (respects .gitignore)."""

from __future__ import annotations

import subprocess


def discover_files(pattern: str = "**/*.py", timeout: int = 30) -> list[str]:
    """Return all git-visible files matching *pattern* — both tracked and
    untracked-but-not-ignored — sorted alphabetically.
    """
    ls_files_output = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            pattern,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout,
    )
    return sorted(f for f in ls_files_output.stdout.strip().splitlines() if f)


def batch(items: list[str], size: int = 3) -> list[list[str]]:
    """Split *items* into consecutive sublists of length *size*; the last chunk may be shorter."""
    return [items[i : i + size] for i in range(0, len(items), size)]
