import sqlite3
from contextlib import contextmanager
from typing import Generator
from backend.app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    """Creates a configured connection to the SQLite database."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(settings.db_path),
        check_same_thread=False,
        timeout=15.0
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for database session."""
    with get_db() as conn:
        yield conn

def init_db() -> None:
    """Initializes the database schema using schema.sql if not initialized."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if assets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets';")
        if not cursor.fetchone():
            if settings.schema_path.exists():
                with open(settings.schema_path, "r", encoding="utf-8") as f:
                    schema_script = f.read()
                conn.executescript(schema_script)
                print("✅ Database initialized successfully from schema.sql.")
            else:
                raise FileNotFoundError(f"schema.sql not found at {settings.schema_path}")
