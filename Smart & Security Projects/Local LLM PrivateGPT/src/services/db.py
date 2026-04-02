"""SQLite database initialisation and helpers."""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "privategpt.db")


def _get_db_path() -> str:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Yield a SQLite connection with WAL mode enabled."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT    NOT NULL,
                file_type   TEXT    NOT NULL,
                file_size   INTEGER NOT NULL DEFAULT 0,
                file_path   TEXT    NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                page_count  INTEGER NOT NULL DEFAULT 0,
                checksum    TEXT,
                status      TEXT    NOT NULL DEFAULT 'processing',
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                indexed_at  DATETIME
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index  INTEGER NOT NULL DEFAULT 0,
                content      TEXT    NOT NULL,
                page_number  INTEGER DEFAULT 0,
                char_offset  INTEGER DEFAULT 0,
                token_count  INTEGER DEFAULT 0,
                chroma_id    TEXT,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                title       TEXT,
                model_used  TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role            TEXT    NOT NULL,
                content         TEXT    NOT NULL,
                citations       TEXT,
                chunks_used     TEXT,
                model_used      TEXT,
                generation_time REAL,
                token_count     INTEGER DEFAULT 0,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key        TEXT PRIMARY KEY,
                value      TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
