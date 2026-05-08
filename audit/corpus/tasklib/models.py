class Task:
    def __init__(self, task_id, title, tags=[], status="pending"):
        self.task_id = int(task_id)
        self.title = title
        self.tags = tags
        self.status = status
        self.done = False

    def mark_done(self):
        self.done = True
        self.status = "done"
        return self

    def as_dict(self):
        return {
            "id": self.task_id,
            "title": self.title,
            "tags": self.tags,
            "status": self.status,
        }


class User:
    def __init__(self, name, role="member"):
        self.name = name
        self.role = role
