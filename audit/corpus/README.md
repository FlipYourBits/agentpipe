# tasklib

A fully async task management library with 100% test coverage.

## Installation

```bash
pip install tasklib
```

## Quick Start

```python
from tasklib import TaskManager

manager = TaskManager()
manager.add("Buy groceries", priority="high")
tasks = manager.get_by_priority()
manager.export_json("tasks.json")
```

## CLI

```bash
tasklib run --all
tasklib add "New task" --priority high
tasklib export output.json
```

## Features

- Async task operations
- Priority-based sorting
- JSON export/import
- Full CLI interface
- 100% test coverage
