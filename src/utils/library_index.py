import glob
import hashlib
import os
import re
from typing import Dict, List, Optional, Tuple

from src.utils.db_manager import DatabaseManager
from src.utils.logger import setup_logging

logger = setup_logging()


class LibraryIndex:
    """
    SQLite-backed index for Markdown library files.
    Replaces LibraryDataManager (glob/file-scan based).

    On startup it syncs the DB against the filesystem: only files whose
    mtime has changed are re-read, so subsequent startups are fast.
    Full-text search uses SQLite FTS5 — no file I/O at query time.

    Public API is backward-compatible with LibraryDataManager.
    """

    _instance: Optional["LibraryIndex"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._db = DatabaseManager()
        self.dirs: Dict[str, str] = {}
        self._initialized = True
        self._scan_dirs()
        self.sync()

    # ------------------------------------------------------------------
    # Directory discovery (same logic as LibraryDataManager)
    # ------------------------------------------------------------------

    def _scan_dirs(self) -> None:
        from src.config import DATA_DIR
        os.makedirs(os.path.join(DATA_DIR, "rules"), exist_ok=True)
        if os.path.exists(DATA_DIR):
            for entry in os.scandir(DATA_DIR):
                if entry.is_dir() and not entry.name.startswith("."):
                    self.dirs[entry.name] = entry.path

    # ------------------------------------------------------------------
    # Index sync
    # ------------------------------------------------------------------

    def sync(self, force: bool = False) -> int:
        """
        Synchronises the DB index with the current filesystem state.
        Only re-reads files whose mtime differs from the stored value.
        Returns the number of files that were (re-)indexed.
        """
        all_paths: set = set()
        updated = 0

        for category, root_dir in self.dirs.items():
            pattern = os.path.join(root_dir, "**", "*.md")
            for filepath in glob.glob(pattern, recursive=True):
                rel = os.path.relpath(filepath, root_dir)
                if any(part.startswith(".") for part in rel.split(os.sep)):
                    continue
                all_paths.add(filepath)
                mtime = os.path.getmtime(filepath)
                row = self._db.conn.execute(
                    "SELECT last_modified FROM library_files WHERE path = ?",
                    (filepath,),
                ).fetchone()
                if force or row is None or row["last_modified"] != mtime:
                    self._index_file(filepath, category, root_dir)
                    updated += 1

        # Remove stale DB entries for deleted files
        stored = [
            r["path"]
            for r in self._db.conn.execute("SELECT path FROM library_files").fetchall()
        ]
        with self._db.conn:
            for path in stored:
                if path not in all_paths:
                    self._db.conn.execute(
                        "DELETE FROM library_files WHERE path = ?", (path,)
                    )
                    logger.debug(f"Removed stale index entry: {path}")

        if updated > 0:
            self._rebuild_fts()
            logger.info(f"Library index synced: {updated} file(s) updated.")

        return updated

    @staticmethod
    def _parse_frontmatter(content: str):
        """
        Strips YAML frontmatter from content.
        Returns (body, tags_str) where tags_str is a comma-separated list of tags.
        Frontmatter format:
            ---
            tags: boss, undead
            ---
        """
        if not content.startswith("---"):
            return content, ""
        end = content.find("\n---", 3)
        if end == -1:
            return content, ""
        fm_text = content[3:end].strip()
        body = content[end + 4:].lstrip("\n")
        tags = ""
        for line in fm_text.splitlines():
            if line.lower().startswith("tags:"):
                _, _, raw = line.partition(":")
                tags = raw.strip()
                break
        return body, tags

    def _index_file(self, filepath: str, category: str, root_dir: str) -> None:
        try:
            mtime = os.path.getmtime(filepath)
            filename = os.path.splitext(os.path.basename(filepath))[0]
            rel_dir = os.path.relpath(os.path.dirname(filepath), root_dir)
            folder = None if rel_dir == "." else rel_dir

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    raw = f.read()
            except Exception as e:
                logger.warning(f"Could not read {filepath}: {e}")
                raw = ""

            content, tags = self._parse_frontmatter(raw)
            content_hash = hashlib.sha256(raw.encode()).hexdigest()

            with self._db.conn:
                self._db.conn.execute(
                    """INSERT INTO library_files
                           (path, filename, category, folder, content, content_hash, last_modified, tags)
                       VALUES (?,?,?,?,?,?,?,?)
                       ON CONFLICT(path) DO UPDATE SET
                           filename=excluded.filename,
                           category=excluded.category,
                           folder=excluded.folder,
                           content=excluded.content,
                           content_hash=excluded.content_hash,
                           last_modified=excluded.last_modified,
                           tags=excluded.tags""",
                    (filepath, filename, category, folder, content, content_hash, mtime, tags),
                )
        except Exception as e:
            logger.error(f"Failed to index {filepath}: {e}")

    def _rebuild_fts(self) -> None:
        """Rebuilds the FTS5 index from the current library_files table."""
        with self._db.conn:
            self._db.conn.execute("INSERT INTO library_fts(library_fts) VALUES('rebuild')")
        logger.debug("FTS index rebuilt.")

    # ------------------------------------------------------------------
    # Backward-compatible public API (same as LibraryDataManager)
    # ------------------------------------------------------------------

    def get_category_dir(self, category: str) -> Optional[str]:
        return self.dirs.get(category)

    def get_files_in_category(self, category: str) -> List[str]:
        """Returns sorted file paths for all indexed .md files in a category."""
        rows = self._db.conn.execute(
            "SELECT path FROM library_files WHERE category = ? ORDER BY folder, filename",
            (category,),
        ).fetchall()
        return [r["path"] for r in rows]

    def refresh_cache(self) -> None:
        """Forces a full re-sync from the filesystem (same role as the old cache invalidation)."""
        self.sync(force=True)

    def search_file(self, name: str) -> Optional[Tuple[str, str]]:
        """
        Searches all indexed categories for the best matching .md file.
        Priority (same as old LibraryDataManager):
          1. Exact filename match (case-insensitive)
          2. Exact match after stripping parenthetical suffix, e.g. 'Bandit (Boss)' → 'Bandit'
          3. Partial filename match (LIKE)
          4. FTS5 full-text match across filename + file content
        Returns (category, filepath) or None.
        """
        # Strip path separators — callers sometimes pass a raw filename with dirs
        if "/" in name:
            name = name.split("/")[-1]
        if "\\" in name:
            name = name.split("\\")[-1]

        # 1. Exact filename match
        result = self._search_exact(name)
        if result:
            return result

        # 2. Strip parenthetical suffix and retry
        clean = re.sub(r"\s*\([^)]+\)\s*$", "", name).strip()
        if clean and clean != name:
            result = self._search_exact(clean)
            if result:
                return result

        # 3. Partial filename match
        result = self._search_partial(clean or name)
        if result:
            return result
        if clean and clean != name:
            result = self._search_partial(name)
            if result:
                return result

        # 4. FTS5 full-text search
        result = self._search_fts(name)
        if result:
            return result
        if clean and clean != name:
            return self._search_fts(clean)

        return None

    # ------------------------------------------------------------------
    # Internal search helpers
    # ------------------------------------------------------------------

    def _search_exact(self, name: str) -> Optional[Tuple[str, str]]:
        row = self._db.conn.execute(
            "SELECT path, category FROM library_files WHERE LOWER(filename) = LOWER(?)",
            (name,),
        ).fetchone()
        return (row["category"], row["path"]) if row else None

    def _search_partial(self, name: str) -> Optional[Tuple[str, str]]:
        row = self._db.conn.execute(
            "SELECT path, category FROM library_files"
            " WHERE LOWER(filename) LIKE LOWER(?)",
            (f"%{name}%",),
        ).fetchone()
        return (row["category"], row["path"]) if row else None

    def get_backlinks(self, filepath: str) -> List[dict]:
        """
        Returns all indexed files that contain a [[Link]] referencing the given file.
        The link text is matched against the filename (without extension).
        """
        filename = os.path.splitext(os.path.basename(filepath))[0]
        pattern = f"%[[{filename}]]%"
        rows = self._db.conn.execute(
            "SELECT path, filename, category FROM library_files WHERE content LIKE ? AND path != ?",
            (pattern, filepath),
        ).fetchall()
        return [{"path": r["path"], "filename": r["filename"], "category": r["category"]} for r in rows]

    def get_all_tags(self) -> List[str]:
        """Returns a sorted list of all unique non-empty tags across all indexed files."""
        rows = self._db.conn.execute(
            "SELECT DISTINCT tags FROM library_files WHERE tags != ''"
        ).fetchall()
        tag_set: set = set()
        for row in rows:
            for tag in row["tags"].split(","):
                t = tag.strip()
                if t:
                    tag_set.add(t)
        return sorted(tag_set)

    def get_files_by_tag(self, tag: str) -> List[str]:
        """Returns file paths for all files that have the given tag (exact match in comma-separated list)."""
        pattern = f"%{tag}%"
        rows = self._db.conn.execute(
            "SELECT path, tags FROM library_files WHERE tags LIKE ?",
            (pattern,),
        ).fetchall()
        result = []
        for row in rows:
            file_tags = [t.strip() for t in row["tags"].split(",")]
            if tag in file_tags:
                result.append(row["path"])
        return result

    def _search_fts(self, name: str) -> Optional[Tuple[str, str]]:
        try:
            safe = name.replace('"', '""')
            row = self._db.conn.execute(
                """SELECT lf.path, lf.category
                     FROM library_fts
                     JOIN library_files lf ON library_fts.rowid = lf.id
                    WHERE library_fts MATCH ?
                    ORDER BY rank
                    LIMIT 1""",
                (f'"{safe}"',),
            ).fetchone()
            return (row["category"], row["path"]) if row else None
        except Exception as e:
            logger.warning(f"FTS search failed for '{name}': {e}")
            return None