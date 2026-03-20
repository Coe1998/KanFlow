"""
KanFlow – Database layer
Uses Python's built-in sqlite3 module (no extra dependencies).
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "kanflow.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


# ---------------------------------------------------------------------------
# Schema bootstrap + migrations
# ---------------------------------------------------------------------------

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                color      TEXT    NOT NULL DEFAULT '#6C63FF',
                notes      TEXT    NOT NULL DEFAULT '',
                created_at TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                status      TEXT    NOT NULL DEFAULT 'todo',
                position    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS labels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name       TEXT    NOT NULL,
                color      TEXT    NOT NULL DEFAULT '#6C63FF'
            );
            CREATE TABLE IF NOT EXISTS task_labels (
                task_id  INTEGER NOT NULL REFERENCES tasks(id)  ON DELETE CASCADE,
                label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, label_id)
            );
            CREATE TABLE IF NOT EXISTS project_files (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                rel_path   TEXT    NOT NULL,
                is_dir     INTEGER NOT NULL DEFAULT 0,
                note       TEXT    NOT NULL DEFAULT '',
                pinned_at  TEXT    NOT NULL,
                UNIQUE(project_id, rel_path)
            );
        """)

        # Safe migrations for existing databases
        proj_cols = [r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()]
        if "notes" not in proj_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
            conn.commit()
        if "git_path" not in proj_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN git_path TEXT NOT NULL DEFAULT ''")
            conn.commit()

        pf_cols = [r[1] for r in conn.execute("PRAGMA table_info(project_files)").fetchall()]
        if "is_dir" not in pf_cols:
            conn.execute("ALTER TABLE project_files ADD COLUMN is_dir INTEGER NOT NULL DEFAULT 0")
            conn.commit()


# ---------------------------------------------------------------------------
# Project helpers
# ---------------------------------------------------------------------------

def _project_stats(conn, project_id):
    row = conn.execute(
        """SELECT
               COUNT(*)                                          AS total,
               SUM(CASE WHEN status='done'        THEN 1 END)  AS done,
               SUM(CASE WHEN status='in_progress' THEN 1 END)  AS in_progress
           FROM tasks WHERE project_id=?""",
        (project_id,)
    ).fetchone()
    total       = row["total"]       or 0
    done        = row["done"]        or 0
    in_progress = row["in_progress"] or 0
    done_pct    = round(done        / total * 100) if total > 0 else 0
    wip_pct     = round(in_progress / total * 100) if total > 0 else 0
    return total, done, in_progress, done_pct, wip_pct


def _project_to_dict(row, conn=None):
    d = dict(row)
    total, done, in_progress, done_pct, wip_pct = (
        _project_stats(conn, d["id"]) if conn else (0, 0, 0, 0, 0)
    )
    d["task_count"]        = total
    d["done_count"]        = done
    d["in_progress_count"] = in_progress
    d["completion_pct"]    = done_pct
    d["in_progress_pct"]   = wip_pct
    return d


def get_all_projects():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [_project_to_dict(r, conn=conn) for r in rows]


def get_project(project_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return _project_to_dict(row, conn=conn) if row else None


def create_project(name, color="#6C63FF"):
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO projects (name, color, created_at) VALUES (?,?,?)", (name, color, now))
        conn.commit()
        return get_project(cur.lastrowid)


def update_project(project_id, name=None, color=None, git_path=None):
    with get_conn() as conn:
        if name is not None:
            conn.execute("UPDATE projects SET name=? WHERE id=?", (name, project_id))
        if color is not None:
            conn.execute("UPDATE projects SET color=? WHERE id=?", (color, project_id))
        if git_path is not None:
            conn.execute("UPDATE projects SET git_path=? WHERE id=?", (git_path.strip(), project_id))
        conn.commit()
    return get_project(project_id)


# ---------------------------------------------------------------------------
# Project-file (pinned file) helpers
# ---------------------------------------------------------------------------

def get_pinned_files(project_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM project_files WHERE project_id=? ORDER BY rel_path",
            (project_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def pin_file(project_id: int, rel_path: str, note: str = "", is_dir: bool = False) -> dict:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO project_files (project_id, rel_path, is_dir, note, pinned_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(project_id, rel_path) DO UPDATE SET note=excluded.note, is_dir=excluded.is_dir""",
            (project_id, rel_path, 1 if is_dir else 0, note, now)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM project_files WHERE project_id=? AND rel_path=?",
            (project_id, rel_path)
        ).fetchone()
        return dict(row)


def unpin_file(project_id: int, rel_path: str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM project_files WHERE project_id=? AND rel_path=?",
            (project_id, rel_path)
        )
        conn.commit()


def update_file_note(project_id: int, rel_path: str, note: str) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE project_files SET note=? WHERE project_id=? AND rel_path=?",
            (note, project_id, rel_path)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM project_files WHERE project_id=? AND rel_path=?",
            (project_id, rel_path)
        ).fetchone()
        return dict(row) if row else None


def get_project_notes(project_id) -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT notes FROM projects WHERE id=?", (project_id,)).fetchone()
        return row["notes"] if row else ""


def set_project_notes(project_id, notes: str) -> str:
    with get_conn() as conn:
        conn.execute("UPDATE projects SET notes=? WHERE id=?", (notes, project_id))
        conn.commit()
    return notes


def delete_project(project_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------

def get_project_labels(project_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM labels WHERE project_id=? ORDER BY name",
            (project_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def create_label(project_id, name, color="#6C63FF"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO labels (project_id, name, color) VALUES (?,?,?)",
            (project_id, name, color)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM labels WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def delete_label(label_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM labels WHERE id=?", (label_id,))
        conn.commit()


def set_task_labels(task_id, label_ids: list[int]):
    """Replace all labels for a task with the given list."""
    with get_conn() as conn:
        conn.execute("DELETE FROM task_labels WHERE task_id=?", (task_id,))
        for lid in label_ids:
            conn.execute(
                "INSERT OR IGNORE INTO task_labels (task_id, label_id) VALUES (?,?)",
                (task_id, lid)
            )
        conn.commit()


def _fetch_labels_for_tasks(conn, task_ids: list[int]) -> dict:
    """Return {task_id: [label_dict, …]} for all given task ids in one query."""
    if not task_ids:
        return {}
    placeholders = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"""SELECT tl.task_id, l.id, l.name, l.color
            FROM task_labels tl
            JOIN labels l ON l.id = tl.label_id
            WHERE tl.task_id IN ({placeholders})
            ORDER BY l.name""",
        task_ids
    ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["task_id"], []).append(
            {"id": r["id"], "name": r["name"], "color": r["color"]}
        )
    return result


# ---------------------------------------------------------------------------
# Task helpers
# ---------------------------------------------------------------------------

def _task_to_dict(row):
    d = dict(row)
    d.setdefault("labels", [])
    return d


def get_tasks(project_id):
    with get_conn() as conn:
        rows  = conn.execute(
            "SELECT * FROM tasks WHERE project_id=? ORDER BY position ASC",
            (project_id,)
        ).fetchall()
        tasks = [_task_to_dict(r) for r in rows]
        if tasks:
            label_map = _fetch_labels_for_tasks(conn, [t["id"] for t in tasks])
            for t in tasks:
                t["labels"] = label_map.get(t["id"], [])
        return tasks


def get_task(task_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None
        task = _task_to_dict(row)
        label_map = _fetch_labels_for_tasks(conn, [task_id])
        task["labels"] = label_map.get(task_id, [])
        return task


def _max_position(conn, project_id, status):
    row = conn.execute(
        "SELECT MAX(position) as m FROM tasks WHERE project_id=? AND status=?",
        (project_id, status)
    ).fetchone()
    return row["m"] if row and row["m"] is not None else 0


def create_task(project_id, title, description="", status="todo"):
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        pos = _max_position(conn, project_id, status) + 1
        cur = conn.execute(
            "INSERT INTO tasks (project_id, title, description, status, position, created_at) VALUES (?,?,?,?,?,?)",
            (project_id, title, description, status, pos, now)
        )
        conn.commit()
        return get_task(cur.lastrowid)


def update_task(task_id, **kwargs):
    task = get_task(task_id)
    if not task:
        return None
    with get_conn() as conn:
        new_status = kwargs.get("status")
        if new_status and new_status != task["status"]:
            kwargs["position"] = _max_position(conn, task["project_id"], new_status) + 1
        allowed = {"title", "description", "status", "position"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if updates:
            sets = ", ".join(f"{k}=?" for k in updates)
            vals = list(updates.values()) + [task_id]
            conn.execute(f"UPDATE tasks SET {sets} WHERE id=?", vals)
            conn.commit()
    return get_task(task_id)


def reorder_tasks(project_id, status, ordered_ids: list[int]):
    with get_conn() as conn:
        for pos, task_id in enumerate(ordered_ids):
            conn.execute(
                "UPDATE tasks SET position=? WHERE id=? AND project_id=? AND status=?",
                (pos, task_id, project_id, status)
            )
        conn.commit()


def delete_task(task_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Demo seed
# ---------------------------------------------------------------------------

def seed_demo_data():
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()["c"]
    if count == 0:
        proj = create_project("My First Project", "#6C63FF")
        pid  = proj["id"]
        create_task(pid, "Welcome to KanFlow!", "Click a card to open the preview. Drag it to move between columns.", "todo")
        create_task(pid, "Create your first project", "Use the + New Project button on the home screen.", "done")
        create_task(pid, "Add team members", "Share the URL with your colleagues.", "in_progress")
