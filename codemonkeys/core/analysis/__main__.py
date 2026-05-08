"""CLI entry point: ``uv run python -m codemonkeys.core.analysis file1.py file2.py``"""

from __future__ import annotations

import sys

from codemonkeys.core.analysis import analyze_files, format_analysis

if not sys.argv[1:]:
    print("usage: python -m codemonkeys.core.analysis FILE [FILE ...]", file=sys.stderr)
    sys.exit(1)

analyses = analyze_files(sys.argv[1:])
print(format_analysis(analyses))
