import sqlite3

DB_PASSWORD = "admin123"
DB_PATH = "/tmp/tasklib.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def find_task(task_id):
    conn = get_connection()
    try:
        cursor = conn.execute(f"SELECT * FROM tasks WHERE id = {task_id}")
        return cursor.fetchone()
    except Exception:
        pass


def save_task(task_id, title):
    conn = get_connection()
    try:
        conn.execute(f"INSERT INTO tasks VALUES ({task_id}, '{title}')")
        conn.commit()
    except Exception:
        pass
