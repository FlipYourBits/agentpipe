"""File discovery via git ls-files (respects .gitignore)."""

from __future__ import annotations

import subprocess


def discover_files(pattern: str = "**/*.py") -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", pattern],
        capture_output=True,
        text=True,
    )
    return sorted(f for f in result.stdout.strip().splitlines() if f)


def batch(items: list[str], size: int = 3) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
