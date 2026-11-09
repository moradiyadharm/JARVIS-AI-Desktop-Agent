"""SQLite storage for JARVIS: conversation memory and the automation history."""
import json
import sqlite3
from datetime import datetime

import config


def _connect():
    return sqlite3.connect(config.DB_PATH)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    """Create the tables if they do not exist yet."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool TEXT NOT NULL,
                args TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


# ---------- conversation memory ----------
def save_message(role, text):
    """Save one message. role is 'user' or 'model'."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (role, text, created_at) VALUES (?, ?, ?)",
            (role, text, _now()),
        )


def get_recent(limit=10):
    """Last few messages, oldest first. Used as JARVIS memory."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, text FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return list(reversed(rows))


def get_history(limit=50):
    """Last messages with time, oldest first. Used for the History view."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT created_at, role, text FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return list(reversed(rows))


def clear_history():
    """Delete all saved conversation messages (automation history is kept)."""
    with _connect() as conn:
        conn.execute("DELETE FROM messages")


# ---------- automation (execution) history ----------
def log_execution(tool, args, status, result=""):
    """Save one action JARVIS tried. status: ok, error, invalid, denied, blocked."""
    try:
        args_text = json.dumps(args, ensure_ascii=False, default=str)
    except Exception:
        args_text = str(args)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO executions (tool, args, status, result, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (tool, args_text, status, str(result)[:500], _now()),
        )


def get_executions(limit=20):
    """Last actions, oldest first: (time, tool, args, status, result)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT created_at, tool, args, status, result FROM executions "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return list(reversed(rows))
