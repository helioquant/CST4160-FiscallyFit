"""
database/db.py
Core database layer: connection management, schema creation, CRUD helpers.
Uses SQLite with WAL mode for better concurrent read performance.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH: str = os.getenv("DB_PATH", "fiscallyfit.db")

# ---------------------------------------------------------------------------
# DDL – table definitions
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT    NOT NULL,
    last_name   TEXT    NOT NULL,
    username    TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    income      REAL    DEFAULT 0.0,
    currency    TEXT    DEFAULT 'GBP',
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    send_home   REAL    DEFAULT 0.0,
    date        TEXT    DEFAULT (date('now')),
    notes       TEXT    DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS savings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    expected    REAL    NOT NULL,
    actual      REAL    NOT NULL,
    month       TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    ticker      TEXT    NOT NULL,
    shares      REAL    NOT NULL,
    added_at    TEXT    DEFAULT (datetime('now')),
    UNIQUE(user_id, ticker),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS emi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    label           TEXT    DEFAULT 'Loan',
    loan_amount     REAL    NOT NULL,
    interest_rate   REAL    NOT NULL,
    tenure          INTEGER NOT NULL,
    currency        TEXT    DEFAULT 'GBP',
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row factory set to dict-like rows."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    """Context manager that yields (conn, cursor), commits on success, rolls back on error."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield conn, cur
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.exception("Database error: %s", exc)
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialise database schema. Safe to call on every startup."""
    with db_cursor() as (conn, cur):
        cur.executescript(SCHEMA_SQL)
    logger.info("Database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Generic CRUD helpers
# ---------------------------------------------------------------------------

def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT query and return a list of row dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute_write(sql: str, params: tuple = ()) -> Optional[int]:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid."""
    with db_cursor() as (conn, cur):
        cur.execute(sql, params)
        return cur.lastrowid
