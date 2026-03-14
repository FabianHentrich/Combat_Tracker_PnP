import os
import sqlite3
from typing import Optional

from src.utils.logger import setup_logging

logger = setup_logging()

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS enemies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    category    TEXT    NOT NULL,
    subcategory TEXT,
    lp          INTEGER NOT NULL,
    rp          INTEGER NOT NULL DEFAULT 0,
    sp          INTEGER NOT NULL DEFAULT 0,
    gew         INTEGER NOT NULL DEFAULT 1,
    char_type   TEXT    NOT NULL DEFAULT 'Gegner',
    level       INTEGER NOT NULL DEFAULT 0,
    init        INTEGER,
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS library_files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    path          TEXT    UNIQUE NOT NULL,
    filename      TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    folder        TEXT,
    content       TEXT    NOT NULL DEFAULT '',
    content_hash  TEXT    NOT NULL DEFAULT '',
    last_modified REAL    NOT NULL DEFAULT 0,
    tags          TEXT    NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE IF NOT EXISTS library_fts USING fts5(
    filename,
    content,
    content='library_files',
    content_rowid='id',
    tokenize='unicode61'
);
"""


class DatabaseManager:
    """
    Singleton that owns the SQLite connection and applies the schema on first use.
    Pass db_path=':memory:' in tests for an isolated in-memory database.
    """

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return

        from src.config import FILES
        self._db_path: str = db_path if db_path is not None else FILES["library_db"]
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = True

        self._connect()
        self._apply_schema()
        self._migrate()

    # ------------------------------------------------------------------
    # Internal setup
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        if self._db_path != ":memory:":
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        logger.info(f"Database opened: {self._db_path}")

    def _apply_schema(self) -> None:
        with self._conn:
            self._conn.executescript(_SCHEMA)
        logger.debug("Database schema applied.")

    def _migrate(self) -> None:
        """Applies incremental schema migrations for existing databases."""
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(library_files)").fetchall()}
        if "tags" not in cols:
            with self._conn:
                self._conn.execute("ALTER TABLE library_files ADD COLUMN tags TEXT NOT NULL DEFAULT ''")
            logger.info("Migration: added 'tags' column to library_files.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        """Closes the connection and resets the singleton so a new instance can be created."""
        if self._conn:
            self._conn.close()
            self._conn = None
        DatabaseManager._instance = None
        self._initialized = False