# tasklib Feature Specification

## Overview

tasklib is a task management library supporting CRUD operations, tagging,
priority sorting, notifications, and data export.

## Features

### 1. CRUD Operations

Create, read, update, and delete tasks. Each task has an id, title, status,
and tags.

- `TaskManager.add(title, tags)` — create a new task
- `TaskManager.get(task_id)` — retrieve a task by id
- `TaskManager.remove(task_id)` — delete a task
- `TaskManager.list_all()` — list all tasks

### 2. Tagging System

Tasks support arbitrary string tags for categorization.

- Tags are passed at creation time
- Tags are stored as a list on each Task
- Support filtering by tag via `TaskManager.filter_by_tag(tag)`

### 3. Priority Sorting

Tasks have a priority field (high/medium/low) with sorting support.

- `Task.priority` field with validation
- `TaskManager.get_by_priority()` — returns tasks sorted by priority

### 4. Notifications

Email notifications when tasks are created or completed.

- `TaskManager.notify(task, event)` — send email notification
- Configurable SMTP settings

### 5. Export to JSON

Export all tasks to a JSON file.

- `TaskManager.export_json(path)` — write all tasks to file
- Include task id, title, tags, status, priority
