import json
import os
from typing import Any, Dict, List, Optional

from src.utils.db_manager import DatabaseManager
from src.utils.logger import setup_logging

logger = setup_logging()


class EnemyRepository:
    """
    Persistent storage for enemy presets backed by SQLite.
    Replaces EnemyDataLoader (JSON-based).

    Public API is backward-compatible with EnemyDataLoader so existing
    controller code (LibraryImportTab etc.) works without changes.
    On first use the repository auto-migrates from enemies.json if the
    table is still empty.
    """

    _instance: Optional["EnemyRepository"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._db = DatabaseManager()
        self._initialized = True
        if self._is_empty():
            self._auto_migrate()

    # ------------------------------------------------------------------
    # Backward-compatible API (same surface as EnemyDataLoader)
    # ------------------------------------------------------------------

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the data dict for a single preset, or None if not found."""
        row = self._db.conn.execute(
            "SELECT * FROM enemies WHERE name = ?", (name,)
        ).fetchone()
        return self._row_to_preset(row) if row else None

    def get_all_presets(self) -> Dict[str, Any]:
        """
        Returns the hierarchical {category: {[subcategory:] {name: data}}} tree
        that LibraryImportTab.populate_tree() expects.
        """
        rows = self._db.conn.execute(
            "SELECT * FROM enemies ORDER BY category, subcategory, name"
        ).fetchall()
        tree: Dict[str, Any] = {}
        for row in rows:
            cat = row["category"]
            sub = row["subcategory"]
            name = row["name"]
            data = self._row_to_preset(row)
            if sub:
                tree.setdefault(cat, {}).setdefault(sub, {})[name] = data
            else:
                tree.setdefault(cat, {})[name] = data
        return tree

    @property
    def flat_presets(self) -> Dict[str, Any]:
        """Flat {name: data} dict for quick single-preset lookup."""
        rows = self._db.conn.execute("SELECT * FROM enemies").fetchall()
        return {row["name"]: self._row_to_preset(row) for row in rows}

    # ------------------------------------------------------------------
    # CRUD (new capability vs. JSON loader)
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        category: str,
        lp: int,
        rp: int = 0,
        sp: int = 0,
        gew: int = 1,
        char_type: str = "Gegner",
        level: int = 0,
        subcategory: Optional[str] = None,
        init: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Inserts a new preset and returns its row id."""
        with self._db.conn:
            cur = self._db.conn.execute(
                """INSERT INTO enemies
                   (name, category, subcategory, lp, rp, sp, gew, char_type, level, init, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (name, category, subcategory, lp, rp, sp, gew, char_type, level, init, notes),
            )
        logger.debug(f"Enemy added: '{name}' (id={cur.lastrowid})")
        return cur.lastrowid

    def update(self, preset_id: int, **kwargs) -> None:
        """Updates named fields of an existing preset by id."""
        allowed = {
            "name", "category", "subcategory", "lp", "rp",
            "sp", "gew", "char_type", "level", "init", "notes",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [preset_id]
        with self._db.conn:
            self._db.conn.execute(
                f"UPDATE enemies SET {set_clause} WHERE id = ?", values
            )
        logger.debug(f"Enemy updated: id={preset_id}, fields={list(fields)}")

    def delete(self, preset_id: int) -> None:
        """Deletes a preset by id."""
        with self._db.conn:
            self._db.conn.execute("DELETE FROM enemies WHERE id = ?", (preset_id,))
        logger.debug(f"Enemy deleted: id={preset_id}")

    # ------------------------------------------------------------------
    # Filtered queries (not possible with the old JSON loader)
    # ------------------------------------------------------------------

    def get_by_filter(
        self,
        category: Optional[str] = None,
        char_type: Optional[str] = None,
        level_min: Optional[int] = None,
        level_max: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Returns all presets matching the given filters."""
        clauses: List[str] = []
        params: List[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if char_type:
            clauses.append("char_type = ?")
            params.append(char_type)
        if level_min is not None:
            clauses.append("level >= ?")
            params.append(level_min)
        if level_max is not None:
            clauses.append("level <= ?")
            params.append(level_max)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._db.conn.execute(
            f"SELECT * FROM enemies {where} ORDER BY category, name", params
        ).fetchall()
        return [self._row_to_preset(r) for r in rows]

    def categories(self) -> List[str]:
        """Returns all distinct top-level category names, sorted."""
        rows = self._db.conn.execute(
            "SELECT DISTINCT category FROM enemies ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]

    # ------------------------------------------------------------------
    # Migration from enemies.json
    # ------------------------------------------------------------------

    def import_from_json(self, filepath: str) -> int:
        """
        One-time migration: reads enemies.json and inserts all presets.
        Skips presets that already exist by name (safe to call multiple times).
        Returns the number of newly inserted rows.
        """
        if not os.path.exists(filepath):
            logger.warning(f"Migration source not found: {filepath}")
            return 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return 0

        inserted = 0
        # Top-level keys ("Gegner", "NPCs") are organisational only;
        # char_type is encoded in each preset's "type" field.
        for _top_key, top_val in data.items():
            for cat_key, cat_val in top_val.items():
                inserted += self._import_group(cat_key, None, cat_val)

        logger.info(f"Migration complete: {inserted} enemies imported from {filepath}")
        return inserted

    def _import_group(
        self, category: str, subcategory: Optional[str], node: Dict[str, Any]
    ) -> int:
        inserted = 0
        for key, val in node.items():
            if "lp" in val:
                # Leaf node → actual preset
                exists = self._db.conn.execute(
                    "SELECT id FROM enemies WHERE name = ?", (key,)
                ).fetchone()
                if not exists:
                    self.add(
                        name=key,
                        category=category,
                        subcategory=subcategory,
                        lp=val.get("lp", 10),
                        rp=val.get("rp", 0),
                        sp=val.get("sp", 0),
                        gew=val.get("gew", 1),
                        char_type=val.get("type", "Gegner"),
                        level=val.get("level", 0),
                        init=val.get("init"),
                        notes=val.get("notes"),
                    )
                    inserted += 1
            else:
                # Group node → recurse; key becomes subcategory
                inserted += self._import_group(category, key, val)
        return inserted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_empty(self) -> bool:
        return self._db.conn.execute("SELECT COUNT(*) FROM enemies").fetchone()[0] == 0

    def _auto_migrate(self) -> None:
        from src.config import FILES
        filepath = FILES.get("enemies", "data/enemies.json")
        count = self.import_from_json(filepath)
        if count:
            logger.info(f"Auto-migrated {count} presets from enemies.json into library.db")

    @staticmethod
    def _row_to_preset(row) -> Dict[str, Any]:
        """Converts a DB row to the preset dict format expected by UI code."""
        d = dict(row)
        # Rename 'char_type' → 'type' for backward compat with LibraryImportTab
        d["type"] = d.pop("char_type", "Gegner")
        return d