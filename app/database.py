"""SQLite connection handling.

Every request gets its own connection (see `get_db`), which is closed
when the request finishes. Rows are returned as `sqlite3.Row`, so they
can be read like dictionaries: row["title"].
"""

import os
import sqlite3
from pathlib import Path
from typing import Iterator

DB_PATH = os.getenv("LIBRARY_DB", "library.db")
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def connect(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str = DB_PATH) -> None:
    """Create tables if they do not exist yet."""
    with connect(path) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: opens a connection for one request."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
