"""Global test fixtures — block real LLM calls and isolate side effects."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _block_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent any test from making real Claude API calls."""

    async def _blocked(**kwargs):
        raise RuntimeError(
            "Tests must not make real LLM calls — patch codemonkeys.core.runner.query"
        )
        yield  # make it an async generator matching query's signature

    monkeypatch.setattr("codemonkeys.core.runner.query", _blocked)


@pytest.fixture(autouse=True)
def _isolate_log_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect make_log_dir to tmp_path so tests don't litter .codemonkeys/logs/."""
    _counter = 0

    def _tmp_log_dir(label: str | None = None) -> Path:
        nonlocal _counter
        _counter += 1
        name = f"{_counter}_{label}" if label else str(_counter)
        d = tmp_path / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    monkeypatch.setattr("codemonkeys.core.types.make_log_dir", _tmp_log_dir)
    monkeypatch.setattr("codemonkeys.core.runner.make_log_dir", _tmp_log_dir)
    monkeypatch.setattr("codemonkeys.cli.make_log_dir", _tmp_log_dir)

