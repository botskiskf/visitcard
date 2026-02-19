"""SQLite storage for search history (query + timestamp)."""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "history.db"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create history table if not exists."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_search(user_id: int, query_text: str) -> None:
    """Append one search to history."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO search_history (user_id, query_text, created_at) VALUES (?, ?, ?)",
            (user_id, query_text, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(user_id: int, limit: int = 20) -> list[tuple[int, str, str]]:
    """Return list of (id, query_text, created_at) for user, newest first."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id, query_text, created_at FROM search_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return cur.fetchall()
    finally:
        conn.close()
