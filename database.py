import sqlite3
import os
from contextlib import contextmanager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


def get_db_connection():
    """Returns a SQLite connection with foreign keys enabled and Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for safe database operations with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(query, args=()):
    """Executes a SELECT query and returns all matching rows as dicts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def query_one(query, args=()):
    """Executes a SELECT query and returns a single row as a dict, or None."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        row = cursor.fetchone()
        return dict(row) if row else None


def execute_stmt(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query and returns the lastrowid and rowcount."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        return {
            'lastrowid': cursor.lastrowid,
            'rowcount': cursor.rowcount
        }


def init_db(reset=False):
    """Initializes the database using schema.sql."""
    if reset and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

    with get_db() as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
    print("[DB] Database initialized successfully at:", DB_PATH)


if __name__ == '__main__':
    init_db()
