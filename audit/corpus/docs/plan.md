# Add JSON Export Feature

## Goal

Add `export_json(path)` method to TaskManager that writes all tasks to a
JSON file.

## Steps

1. Add `export_json(path: str)` method to `TaskManager` in `tasklib/manager.py`
   - Serialize all tasks from `_tasks` to a list of dicts
   - Each dict: `{"id": task_id, "title": title, "tags": tags, "done": done}`
   - Write to the given path using `json.dump`

2. Write tests for `export_json` in `tests/test_tasks.py`
   - Test export creates a valid JSON file
   - Test export with empty task list
   - Test export with multiple tasks

3. Update `README.md` with export documentation
