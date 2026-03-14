import random
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional

from src.core.mechanics import wuerfle_initiative
from src.models.character import Character
from src.models.enums import CharacterType
from src.config import FONTS, FILES
from src.config.defaults import MAX_GEW
from src.utils.enemy_repository import EnemyRepository
from src.utils.localization import translate
from src.utils.logger import setup_logging

logger = setup_logging()


class LibraryImportTab:
    """
    Controller für den 'Gegner Import' Tab in der Bibliothek.
    Bietet Textsuche, SQL-Filter (Kategorie / Typ / Level-Range)
    und einen Encounter-Generator.
    """

    def __init__(
        self,
        parent: ttk.Widget,
        engine,
        history_manager,
        colors: Dict[str, str],
        close_callback: Callable,
    ):
        self.parent = parent
        self.engine = engine
        self.history_manager = history_manager
        self.colors = colors
        self.close_callback = close_callback

        self.data_loader = EnemyRepository()
        self.enemy_presets = self.data_loader.get_all_presets()
        self.flat_presets = self.data_loader.flat_presets

        self.staging_entries: List[Dict[str, Any]] = []
        self.tree: Optional[ttk.Treeview] = None

        # Search + filter state
        self.search_var = tk.StringVar()
        self.filter_category_var = tk.StringVar(value=translate("library.filter_category_all"))
        self.filter_type_var = tk.StringVar(value=translate("library.filter_type_all"))
        self.filter_level_min_var = tk.StringVar(value="")
        self.filter_level_max_var = tk.StringVar(value="")

        self.scrollable_frame: Optional[ttk.Frame] = None
        self.canvas: Optional[tk.Canvas] = None

        self.setup_ui()

    # ------------------------------------------------------------------
    # Backward-compatible accessor
    # ------------------------------------------------------------------

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        return self.data_loader.get_preset(name)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def setup_ui(self) -> None:
        paned = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---- Left: selection tree ----
        left_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(left_frame, weight=1)

        ttk.Label(
            left_frame,
            text=translate("library.available_enemies"),
            font=FONTS["large"],
        ).pack(pady=(5, 2))

        self._build_search_bar(left_frame)
        self._build_filter_panel(left_frame)
        self._build_tree(left_frame)
        self._build_encounter_generator(left_frame)

        ttk.Button(
            left_frame,
            text=translate("library.add_btn"),
            command=self.add_selected_to_staging,
        ).pack(fill=tk.X, padx=5, pady=(4, 5))

        # ---- Right: staging area ----
        right_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(right_frame, weight=2)

        ttk.Label(
            right_frame,
            text=translate("library.staging_area"),
            font=FONTS["large"],
        ).pack(pady=5)

        self.canvas = tk.Canvas(right_frame, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        self.create_staging_headers()

        # Footer
        btn_frame = ttk.Frame(self.parent, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Button(
            btn_frame,
            text=translate("library.add_all_to_combat"),
            command=self.finalize_import,
        ).pack(side="right")
        ttk.Button(
            btn_frame,
            text=translate("common.cancel"),
            command=self.close_callback,
        ).pack(side="right", padx=10)

    def _build_search_bar(self, parent: ttk.Frame) -> None:
        search_frame = ttk.Frame(parent, style="Card.TFrame")
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 3))
        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT, padx=(5, 2))
        self.search_var.trace("w", self._on_filter_change)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )

    def _build_filter_panel(self, parent: ttk.Frame) -> None:
        filter_frame = ttk.LabelFrame(parent, text="Filter", padding=4)
        filter_frame.pack(fill=tk.X, padx=5, pady=(0, 4))

        # Row 1: Category + Type
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=(0, 3))

        categories = [translate("library.filter_category_all")] + self.data_loader.categories()
        cat_cb = ttk.Combobox(
            row1, textvariable=self.filter_category_var,
            values=categories, state="readonly", width=18,
        )
        cat_cb.pack(side=tk.LEFT, padx=(0, 5))
        cat_cb.bind("<<ComboboxSelected>>", self._on_filter_change)

        type_options = [
            translate("library.filter_type_all"),
            translate("character_types.ENEMY"),
            translate("character_types.NPC"),
            translate("character_types.PLAYER"),
        ]
        type_cb = ttk.Combobox(
            row1, textvariable=self.filter_type_var,
            values=type_options, state="readonly", width=12,
        )
        type_cb.pack(side=tk.LEFT)

        # Row 2: Level range + Reset
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X)

        ttk.Label(row2, text=translate("library.filter_level_label")).pack(side=tk.LEFT)
        self.filter_level_min_var.trace("w", self._on_filter_change)
        ttk.Entry(row2, textvariable=self.filter_level_min_var, width=4).pack(side=tk.LEFT, padx=(3, 2))
        ttk.Label(row2, text=translate("library.filter_level_to")).pack(side=tk.LEFT)
        self.filter_level_max_var.trace("w", self._on_filter_change)
        ttk.Entry(row2, textvariable=self.filter_level_max_var, width=4).pack(side=tk.LEFT, padx=(2, 8))

        ttk.Button(
            row2, text=translate("library.filter_reset"), command=self._reset_filters, width=16
        ).pack(side=tk.LEFT)

    def _build_tree(self, parent: ttk.Frame) -> None:
        self.tree = ttk.Treeview(parent, selectmode="browse", show="tree headings")
        self.tree.heading("#0", text=translate("library.category_header"), anchor="w")

        tree_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=3)

        if self.enemy_presets:
            try:
                self.populate_tree(self.enemy_presets)
            except Exception as e:
                logger.error(f"Fehler beim Befüllen des Baums: {e}")
                self.tree.insert("", "end", text=translate("messages.error_loading"), tags=("error",))
        else:
            self.tree.insert(
                "", "end",
                text=translate("messages.no_enemies_found", file=FILES["enemies"]),
                tags=("error",),
            )

        self.tree.bind("<Double-1>", lambda e: self.add_selected_to_staging())

    def _build_encounter_generator(self, parent: ttk.Frame) -> None:
        enc_frame = ttk.LabelFrame(
            parent, text=translate("library.encounter_generator"), padding=4
        )
        enc_frame.pack(fill=tk.X, padx=5, pady=(4, 2))

        ttk.Label(enc_frame, text=translate("library.encounter_count")).pack(side=tk.LEFT)
        self._enc_count_var = tk.StringVar(value="3")
        ttk.Entry(enc_frame, textvariable=self._enc_count_var, width=4).pack(side=tk.LEFT, padx=(3, 8))
        ttk.Button(
            enc_frame,
            text=translate("library.encounter_generate"),
            command=self._generate_encounter,
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Filter logic
    # ------------------------------------------------------------------

    def _on_filter_change(self, *_args) -> None:
        """Called whenever any filter or the search text changes."""
        filtered = self._get_filtered_presets()
        for item in self.tree.get_children():
            self.tree.delete(item)
        if filtered:
            self.populate_tree(filtered)
            self._expand_all_nodes()
        else:
            self.tree.insert("", "end", text=translate("library.encounter_no_presets"), tags=("error",))

    def _get_filtered_presets(self) -> Dict[str, Any]:
        """
        Combines SQL filter (category / type / level) with optional text search.
        Returns the tree-compatible nested dict.
        """
        # Resolve SQL filter parameters
        all_cat_label = translate("library.filter_category_all")
        all_type_label = translate("library.filter_type_all")

        category = None
        raw_cat = self.filter_category_var.get()
        if raw_cat and raw_cat != all_cat_label:
            category = raw_cat

        char_type = None
        raw_type = self.filter_type_var.get()
        if raw_type and raw_type != all_type_label:
            # Convert display label back to enum value
            type_map = {
                translate(f"character_types.{t.name}"): t.value for t in CharacterType
            }
            char_type = type_map.get(raw_type)

        level_min = level_max = None
        try:
            val = self.filter_level_min_var.get().strip()
            if val:
                level_min = int(val)
        except ValueError:
            pass
        try:
            val = self.filter_level_max_var.get().strip()
            if val:
                level_max = int(val)
        except ValueError:
            pass

        # Fetch from DB if any SQL filter is active, otherwise use cached full tree
        sql_active = any(x is not None for x in (category, char_type, level_min, level_max))
        if sql_active:
            rows = self.data_loader.get_by_filter(
                category=category, char_type=char_type,
                level_min=level_min, level_max=level_max,
            )
            tree = self._build_tree_from_rows(rows)
        else:
            tree = self.enemy_presets

        # Apply text search on top
        query = self.search_var.get().strip().lower()
        if query:
            tree = self._filter_data_recursive(tree, query)

        return tree

    @staticmethod
    def _build_tree_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reconstructs the nested tree structure from a flat list of DB rows."""
        tree: Dict[str, Any] = {}
        for row in rows:
            cat = row.get("category", "?")
            sub = row.get("subcategory")
            name = row["name"]
            if sub:
                tree.setdefault(cat, {}).setdefault(sub, {})[name] = row
            else:
                tree.setdefault(cat, {})[name] = row
        return tree

    def _reset_filters(self) -> None:
        self.filter_category_var.set(translate("library.filter_category_all"))
        self.filter_type_var.set(translate("library.filter_type_all"))
        self.filter_level_min_var.set("")
        self.filter_level_max_var.set("")
        self.search_var.set("")

    # ------------------------------------------------------------------
    # Encounter generator
    # ------------------------------------------------------------------

    def _generate_encounter(self) -> None:
        try:
            count = max(1, int(self._enc_count_var.get()))
        except ValueError:
            count = 1

        pool = self._flat_from_filtered(self._get_filtered_presets())
        if not pool:
            messagebox.showinfo(
                translate("dialog.info.title"),
                translate("library.encounter_no_presets"),
            )
            return

        picks = random.choices(list(pool.items()), k=count)
        for name, data in picks:
            self.add_staging_row(name, data)

    @staticmethod
    def _flat_from_filtered(tree: Dict[str, Any]) -> Dict[str, Any]:
        """Flattens the filtered tree into a {name: data} dict for random selection."""
        flat: Dict[str, Any] = {}
        for val in tree.values():
            if "lp" in val:
                # shouldn't happen at top level, but handle it
                flat[val.get("name", "?")] = val
            else:
                for k2, v2 in val.items():
                    if "lp" in v2:
                        flat[k2] = v2
                    else:
                        for k3, v3 in v2.items():
                            if "lp" in v3:
                                flat[k3] = v3
        return flat

    # ------------------------------------------------------------------
    # Tree helpers
    # ------------------------------------------------------------------

    def populate_tree(self, data: Dict[str, Any], parent: str = "") -> None:
        for key, value in sorted(data.items()):
            if "lp" in value:
                self.tree.insert(parent, "end", text=key, values=("enemy",), tags=("enemy",))
            else:
                node = self.tree.insert(parent, "end", text=key, open=False, tags=("category",))
                self.populate_tree(value, node)

    def search(self, query: str) -> int:
        """Called by global search in LibraryHandler. Returns matched enemy count."""
        self.search_var.set(query)
        return self._count_leaves()

    def _filter_data_recursive(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in data.items():
            if "lp" in value:
                if query in key.lower():
                    result[key] = value
            else:
                filtered = self._filter_data_recursive(value, query)
                if filtered:
                    result[key] = filtered
        return result

    def _expand_all_nodes(self, parent: str = "") -> None:
        for item in self.tree.get_children(parent):
            self.tree.item(item, open=True)
            self._expand_all_nodes(item)

    def _count_leaves(self, parent: str = "") -> int:
        count = 0
        for item in self.tree.get_children(parent):
            if "enemy" in self.tree.item(item, "tags"):
                count += 1
            else:
                count += self._count_leaves(item)
        return count

    # ------------------------------------------------------------------
    # Staging area
    # ------------------------------------------------------------------

    def add_selected_to_staging(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item_text = self.tree.item(selected[0], "text")
        if "enemy" in self.tree.item(selected[0], "tags"):
            data = self.flat_presets.get(item_text) or self.data_loader.get_preset(item_text)
            if data:
                self.add_staging_row(item_text, data)

    def create_staging_headers(self) -> None:
        header_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)
        headers = [
            translate("character_attributes.name"),
            translate("character_attributes.type"),
            translate("character_attributes.lp"),
            translate("character_attributes.rp"),
            translate("character_attributes.sp"),
            translate("character_attributes.gew"),
            translate("character_attributes.level"),
            translate("dialog.import_preview.count"),
            translate("library.act_immediately"),
            "",
        ]
        widths = [30, 10, 5, 5, 5, 5, 5, 5, 5, 5]
        for col, width in zip(headers, widths):
            ttk.Label(header_frame, text=col, font=FONTS["small"], width=width, anchor="w").pack(
                side="left", padx=2
            )

    def add_staging_row(self, name: str, data: Dict[str, Any]) -> None:
        row_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        row_frame.pack(fill="x", pady=5)

        e_name = ttk.Entry(row_frame, width=30)
        e_name.insert(0, name)
        e_name.pack(side="left", padx=5)

        translated_types = {translate(f"character_types.{t.name}"): t.value for t in CharacterType}
        e_type = ttk.Combobox(row_frame, values=list(translated_types.keys()), width=10, state="readonly")
        e_type.set(translate(f"character_types.{data.get('type', CharacterType.ENEMY.value)}"))
        e_type.pack(side="left", padx=5)

        fields = {}
        for attr, default in (("lp", 10), ("rp", 0), ("sp", 0), ("gew", 1), ("level", 0)):
            entry = ttk.Entry(row_frame, width=5)
            entry.insert(0, str(data.get(attr, default)))
            entry.pack(side="left", padx=5)
            fields[attr] = entry

        e_count = ttk.Entry(row_frame, width=5)
        e_count.insert(0, "1")
        e_count.pack(side="left", padx=5)

        var_surprise = tk.BooleanVar()
        ttk.Checkbutton(row_frame, variable=var_surprise).pack(side="left", padx=5)

        btn_del = ttk.Button(row_frame, text="X", width=3)
        btn_del.pack(side="left", padx=5)

        entry_obj = {
            "frame": row_frame, "name": e_name, "type": e_type,
            "lp": fields["lp"], "rp": fields["rp"], "sp": fields["sp"],
            "gew": fields["gew"], "level": fields["level"],
            "count": e_count, "surprise": var_surprise,
            "translated_types": translated_types,
        }
        btn_del.configure(command=lambda: self.remove_staging_row(row_frame, entry_obj))
        self.staging_entries.append(entry_obj)

    def remove_staging_row(self, frame: ttk.Frame, entry_obj: Dict[str, Any]) -> None:
        frame.destroy()
        if entry_obj in self.staging_entries:
            self.staging_entries.remove(entry_obj)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def finalize_import(self) -> None:
        if not self.staging_entries:
            return
        count_imported = 0
        self.history_manager.save_snapshot()
        try:
            for entry in self.staging_entries:
                try:
                    count = int(entry["count"].get())
                except ValueError:
                    count = 1
                if count <= 0:
                    continue

                name_base = entry["name"].get()
                char_type_value = entry["translated_types"].get(
                    entry["type"].get(), CharacterType.ENEMY.value
                )
                lp = int(entry["lp"].get())
                rp = int(entry["rp"].get())
                sp = int(entry["sp"].get())
                gew = min(int(entry["gew"].get()), MAX_GEW)
                level = int(entry["level"].get())
                surprise = entry["surprise"].get()

                for i in range(count):
                    final_name = f"{name_base} {i + 1}" if count > 1 else name_base
                    new_char = Character(
                        final_name, lp, rp, sp,
                        wuerfle_initiative(gew),
                        gew=gew, char_type=char_type_value, level=level,
                    )
                    self.engine.insert_character(new_char, surprise=surprise)
                    count_imported += 1

            self.engine.log(translate("messages.characters_added_from_library", count=count_imported))
            self.close_callback()
        except ValueError:
            messagebox.showerror(
                translate("dialog.error.title"),
                translate("messages.use_valid_numbers"),
            )

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def update_colors(self, colors: Dict[str, str]) -> None:
        self.colors = colors
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.configure(bg=self.colors["panel"])