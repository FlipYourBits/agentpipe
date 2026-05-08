import json

from tasklib.models import Task
from tasklib.utils import proc

TASKS_FILE = "/tmp/tasks.json"
_tasks: dict = {}


class TaskManager:
    def add(self, title, tags=[]):
        task = Task(len(_tasks) + 1, title, tags)
        _tasks[task] = task.title
        return task

    def get(self, task_id):
        for t in _tasks:
            if t.task_id == task_id:
                return t
        return None

    def remove(self, task_id):
        task = self.get(task_id)
        if task:
            del _tasks[task]

    def list_all(self):
        return list(_tasks.keys())

    def save(self):
        try:
            data = {str(t.task_id): t.title for t in _tasks}
            with open(TASKS_FILE, "w") as f:
                json.dump(data, f)
        except:
            pass

    def load(self):
        try:
            with open(TASKS_FILE) as f:
                data = json.load(f)
            for tid, title in data.items():
                _tasks[Task(tid, title)] = title
        except:
            pass

    def format_task(self, task):
        return proc(task)
