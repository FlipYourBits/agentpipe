## Python Guidelines

### Imports & Module Structure

- Use `from __future__ import annotations` in every file.
- Group imports: stdlib, third-party, local — separated by blank lines.
- Prefer absolute imports over relative. Use relative only within a package's internals.
- Don't import from deeply nested private modules across package boundaries.

```python
# Bad
from codemonkeys.core.runner import _estimate_cost
import os, sys, json

# Good
import json
import os
import sys

from codemonkeys.core.runner import run_agent
```

### Type Hints

- Type-hint every public function and method. Use `Literal` types for constrained string params.
- Use `TypeAlias` for complex types that repeat.
- Prefer `X | None` over `Optional[X]`.
- Use `Self` return type for fluent/builder methods.
- Never use `Any` unless you genuinely mean "any type" — prefer `object` or a protocol.

```python
# Bad
def process(data, mode="fast"):
    ...

# Good
from typing import Literal
Mode = Literal["fast", "thorough"]

def process(data: InputModel, mode: Mode = "fast") -> Result:
    ...
```

### Data Modeling

- Use Pydantic `BaseModel` for structured data with validation, not ad-hoc dicts.
- Use `@dataclass(frozen=True)` for simple records without validation.
- Use `TypedDict` when you need dict compatibility (JSON responses, legacy APIs).
- Never pass dicts with implicit schemas between functions.

```python
# Bad
def create_user(data: dict) -> dict:
    return {"id": generate_id(), "name": data["name"]}

# Good
class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: str
    name: str
    email: str

def create_user(data: UserCreate) -> User:
    return User(id=generate_id(), name=data.name, email=data.email)
```

### Functions

- Keep functions short and single-purpose. If a function exceeds ~40 lines or three nesting levels, extract a helper.
- Name things for what they mean, not what they are.
- Prefer pure functions and explicit dependencies. Side effects belong at the edges of the program.
- Use keyword-only arguments (`*`) for functions with more than 2 parameters.

```python
# Bad
def send(msg, addr, port, timeout, retries, use_tls):
    ...

# Good
def send(
    message: Message,
    *,
    destination: Address,
    timeout: float = 30.0,
    retries: int = 3,
    use_tls: bool = True,
) -> SendResult:
    ...
```

### Error Handling

- Don't catch `Exception` broadly. Catch the narrowest type you can name and let the rest crash.
- Don't write defensive code for situations that cannot occur given the call graph.
- Use custom exceptions for domain errors — don't repurpose built-in exceptions.
- Never silently swallow exceptions. At minimum, log them.

```python
# Bad
try:
    result = do_everything()
except Exception:
    return None

# Good
try:
    result = parse_config(path)
except FileNotFoundError:
    raise ConfigError(f"Config not found: {path}") from None
except tomllib.TOMLDecodeError as exc:
    raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc
```

### Async Patterns

- Always `await` coroutines. A bare coroutine call returns a coroutine object, not the result.
- Use `asyncio.TaskGroup` (3.11+) over `asyncio.gather` for structured concurrency.
- Never call blocking I/O inside `async def` — use `asyncio.to_thread()`.
- Use `async with` for async context managers. Don't forget to close async resources.

```python
# Bad — blocks the event loop
async def fetch_data():
    response = requests.get(url)  # BLOCKING
    return response.json()

# Good
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Bad — unstructured concurrency
results = await asyncio.gather(*tasks)  # one failure kills all

# Good — structured concurrency with error isolation
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(process(item)) for item in items]
results = [t.result() for t in tasks]
```

### Context Managers & Resources

- Use `with` for any resource that has a `close()`.
- Write custom context managers with `@contextmanager` for setup/teardown patterns.
- Use `contextlib.suppress` instead of empty `except` blocks for expected exceptions.

```python
# Bad
f = open(path)
data = f.read()
f.close()

# Good
with open(path) as f:
    data = f.read()

# Bad
try:
    os.remove(path)
except FileNotFoundError:
    pass

# Good
with contextlib.suppress(FileNotFoundError):
    os.remove(path)
```

### Iterators & Generators

- Use generators for lazy evaluation of large sequences.
- Prefer `itertools` over manual iteration for common patterns.
- Use generator expressions over list comprehensions when you only iterate once.

```python
# Bad — builds entire list in memory
all_lines = [line.strip() for line in open(huge_file)]
matches = [l for l in all_lines if "ERROR" in l]

# Good — lazy, streams through the file
def error_lines(path: Path):
    with open(path) as f:
        for line in f:
            if "ERROR" in line:
                yield line.strip()
```

### Testing

- Test behavior, not implementation. Tests should survive refactors.
- Use `pytest.raises` with `match=` to verify exception messages.
- Use `tmp_path` fixture for filesystem tests — never write to the real filesystem.
- Prefer factory fixtures over complex setup.

```python
# Bad — tests implementation detail
def test_user_creation():
    user = create_user(name="Alice")
    assert user._internal_id is not None  # testing private state

# Good — tests behavior
def test_user_creation():
    user = create_user(name="Alice")
    assert user.name == "Alice"
    assert user.id  # truthy, non-empty
```

### Style & Conventions

- Use `pathlib.Path` over `os.path` string juggling.
- Use f-strings, not `.format()` or `%` formatting.
- Comments explain *why* — a non-obvious constraint, a workaround, a subtle invariant. Not what.
- Match the surrounding codebase's style (formatter, import order, naming) over your own preferences.
- No dead code, no commented-out blocks, no `# TODO` without a concrete plan attached.

When refactoring, change behavior in the smallest diff that works. Avoid drive-by reformatting in the same change as a logic edit.
