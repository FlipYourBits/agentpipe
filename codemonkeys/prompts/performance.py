"""Performance review checklist — inefficiency patterns in Python code."""

from __future__ import annotations

PERFORMANCE_REVIEW = """\
## Performance

### data_structures

- Using `list` for membership checks — should be `set` or `dict` when the collection is
  built once and queried repeatedly
- Repeatedly building the same collection instead of caching it
- Sorting or searching an entire collection when only min/max/first-match is needed
- Growing a `list` with repeated `.append()` inside a tight loop when the final size is
  known — suggest a list comprehension or `itertools`

### string_handling

- String concatenation in a loop (`result += chunk`) — quadratic cost, suggest
  `"".join(parts)` or `io.StringIO`
- Repeated regex compilation — `re.compile()` the pattern once at module level

### io_and_network

- Reading an entire large file into memory when line-by-line streaming suffices
- Synchronous blocking I/O inside `async def` — blocks the event loop, use
  `asyncio.to_thread()` or an async library
- Sequential HTTP/network calls that could be concurrent via `asyncio.gather()`
- Missing connection pooling for repeated HTTP or DB calls

### computation

- Redundant work inside a loop — invariant computation that should be hoisted out
- N+1 query patterns — loading related objects one at a time inside a loop
- Expensive operations (file reads, subprocess calls, deep copies) repeated when
  the result could be cached or passed as a parameter
- Quadratic algorithms where a linear or log-linear approach exists

### imports_and_startup

- Heavy imports at module level that are only used in rare code paths — suggest
  local/lazy imports
- Module-level computation (building large dicts, reading config files) that runs
  on import even when the module is imported for a single function

## Exclusions — DO NOT REPORT

These belong to other review categories:
- Missing `await` on coroutines (RESILIENCE_REVIEW owns correctness of async code)
- Missing timeouts or retries (RESILIENCE_REVIEW owns error recovery)
- Premature generalization or over-engineering (CODE_REVIEW owns complexity)
- Micro-optimizations with no measurable impact (do not report these at all)"""
