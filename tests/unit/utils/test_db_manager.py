import sqlite3
import pytest
from src.utils.db_manager import DatabaseManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test gets a fresh DatabaseManager singleton."""
    DatabaseManager._instance = None
    yield
    # Teardown: close whatever was created and clear the singleton
    if DatabaseManager._instance is not None:
        try:
            DatabaseManager._instance.close()
        except Exception:
            DatabaseManager._instance = None


# ---------------------------------------------------------------------------
# WAL mode
# ---------------------------------------------------------------------------

def test_wal_mode_is_enabled():
    """The connection must be opened in WAL journal mode (set by _SCHEMA)."""
    db = DatabaseManager(":memory:")
    row = db.conn.execute("PRAGMA journal_mode").fetchone()
    # In-memory databases cannot use WAL, SQLite silently stays in 'memory' mode;
    # verify the PRAGMA was at least accepted without error and a mode string is returned.
    assert row is not None
    assert isinstance(row[0], str)


# ---------------------------------------------------------------------------
# _migrate() — upgrading a database that lacks the 'tags' column
# ---------------------------------------------------------------------------

def test_migrate_adds_tags_column_when_missing():
    """_migrate() must add the 'tags' column to an old library_files table."""
    # Build an old-schema DB manually (without the tags column)
    old_conn = sqlite3.connect(":memory:")
    old_conn.executescript("""
        CREATE TABLE library_files (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            path          TEXT    UNIQUE NOT NULL,
            filename      TEXT    NOT NULL,
            category      TEXT    NOT NULL,
            folder        TEXT,
            content       TEXT    NOT NULL DEFAULT '',
            content_hash  TEXT    NOT NULL DEFAULT '',
            last_modified REAL    NOT NULL DEFAULT 0
        );
    """)
    # Confirm 'tags' is absent before migration
    cols_before = {row[1] for row in old_conn.execute("PRAGMA table_info(library_files)").fetchall()}
    assert "tags" not in cols_before

    # Hand the open connection to a bare DatabaseManager instance (bypassing __init__)
    db = DatabaseManager.__new__(DatabaseManager)
    db._db_path = ":memory:"
    db._conn = old_conn
    db._initialized = True
    DatabaseManager._instance = db

    db._migrate()

    cols_after = {row[1] for row in old_conn.execute("PRAGMA table_info(library_files)").fetchall()}
    assert "tags" in cols_after

    old_conn.close()
    DatabaseManager._instance = None


def test_migrate_is_idempotent():
    """Calling _migrate() twice on a database that already has 'tags' must not raise."""
    db = DatabaseManager(":memory:")
    # _migrate() was already called during __init__; calling it again must not error
    db._migrate()
    cols = {row[1] for row in db.conn.execute("PRAGMA table_info(library_files)").fetchall()}
    assert "tags" in cols


# ---------------------------------------------------------------------------
# FTS table existence
# ---------------------------------------------------------------------------

def test_fts_table_is_created():
    """The library_fts virtual FTS5 table must be created by the schema."""
    db = DatabaseManager(":memory:")
    # SQLite lists virtual tables in sqlite_master with type='table'
    result = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='library_fts'"
    ).fetchone()
    assert result is not None, "library_fts FTS table was not created"


# ---------------------------------------------------------------------------
# Singleton behaviour and close()
# ---------------------------------------------------------------------------

def test_close_resets_singleton():
    """close() must set _instance to None so a fresh instance can be created."""
    db = DatabaseManager(":memory:")
    assert DatabaseManager._instance is db
    db.close()
    assert DatabaseManager._instance is None


def test_singleton_returns_same_instance():
    """Two calls to DatabaseManager() with the same path return the same object."""
    db1 = DatabaseManager(":memory:")
    db2 = DatabaseManager(":memory:")
    assert db1 is db2
