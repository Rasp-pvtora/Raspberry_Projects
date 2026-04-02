"""SQLite database — recognition log, learning progress, settings."""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sign_language.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_db():
    """Yield a database connection with row factory."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recognition_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sign_label TEXT NOT NULL,
                confidence REAL NOT NULL,
                language TEXT NOT NULL,
                sentence TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sign_label TEXT NOT NULL,
                language TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                last_practiced DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def log_recognition(sign_label: str, confidence: float, language: str, sentence: str = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO recognition_log (sign_label, confidence, language, sentence) VALUES (?, ?, ?, ?)",
            (sign_label, confidence, language, sentence),
        )


def get_recognition_history(limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM recognition_log ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def update_learning_progress(sign_label: str, language: str, correct: bool):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM learning_progress WHERE sign_label = ? AND language = ?",
            (sign_label, language),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE learning_progress
                   SET attempts = attempts + 1,
                       correct = correct + ?,
                       last_practiced = CURRENT_TIMESTAMP
                   WHERE sign_label = ? AND language = ?""",
                (1 if correct else 0, sign_label, language),
            )
        else:
            conn.execute(
                "INSERT INTO learning_progress (sign_label, language, attempts, correct) VALUES (?, ?, 1, ?)",
                (sign_label, language, 1 if correct else 0),
            )


def get_learning_progress(language: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM learning_progress WHERE language = ? ORDER BY sign_label",
            (language,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_setting(key: str, default: str = None) -> str | None:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP""",
            (key, value),
        )
