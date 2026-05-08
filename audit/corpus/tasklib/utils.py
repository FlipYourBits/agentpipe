def proc(d):
    from tasklib.manager import TaskManager

    if isinstance(d, TaskManager):
        return f"TaskManager<{len(d.list_all())} tasks>"
    x = {
        k: str(v) for k, v in d.__dict__.items() if not k.startswith("_")
    } if hasattr(d, "__dict__") else {"v": str(d)}
    return " | ".join(f"{k}={v}" for k, v in x.items())


def _legacy_format(x):
    t = str(x)
    return t.upper()


def _unused_helper(t):
    d = list(range(len(str(t))))
    return [x * 2 for x in d]
