import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional, Callable
from src.models.character import Character
from src.core.mechanics import wuerfle_initiative
from src.utils.logger import setup_logging
from src.models.enums import CharacterType
from src.config import FONTS, FILES
from src.utils.enemy_data_loader import EnemyDataLoader
from src.config.defaults import MAX_GEW

logger = setup_logging()

class LibraryImportTab:
    """
    Controller für den 'Gegner Import' Tab in der Bibliothek.
    Verwaltet die Auswahl von Presets und die Staging-Area.
    """
    def __init__(self, parent: ttk.Widget, engine, history_manager, colors: Dict[str, str], close_callback: Callable):
        self.parent = parent
        self.engine = engine
        self.history_manager = history_manager
        self.colors = colors
        self.close_callback = close_callback

        self.data_loader = EnemyDataLoader()
        self.enemy_presets = self.data_loader.get_all_presets()
        self.flat_presets = self.data_loader.flat_presets

        self.staging_entries: List[Dict[str, Any]] = []

        self.tree: Optional[ttk.Treeview] = None
        self.search_var = tk.StringVar()
        self.scrollable_frame: Optional[ttk.Frame] = None

        self.setup_ui()

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Gibt die Daten eines Presets zurück."""
        return self.data_loader.get_preset(name)

    def setup_ui(self):
        # Layout: Links Baumstruktur (Auswahl), Rechts Liste (Bearbeitung/Anzahl)
        paned = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Linke Seite: Auswahl ---
        left_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Verfügbare Gegner", font=FONTS["large"]).pack(pady=5)

        # --- Suchfeld ---
        search_frame = ttk.Frame(left_frame, style="Card.TFrame")
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT, padx=(5, 2))
        self.search_var.trace("w", self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        # ----------------

        # Treeview für Kategorien
        self.tree = ttk.Treeview(left_frame, selectmode="browse", show="tree headings")
        self.tree.heading("#0", text="Kategorie / Name", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar für Treeview
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if not self.enemy_presets:
            self.tree.insert("", "end", text=f"Keine Gegner gefunden ({FILES['enemies']} prüfen)", tags=("error",))
        else:
            try:
                self.populate_tree(self.enemy_presets)
            except Exception as e:
                logger.error(f"Fehler beim Befüllen des Baums: {e}")
                self.tree.insert("", "end", text="Fehler beim Laden", tags=("error",))

        # Doppelklick fügt zur Liste hinzu
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Button zum Hinzufügen
        ttk.Button(left_frame, text="Hinzufügen ->", command=self.add_selected_to_staging).pack(fill=tk.X, padx=5, pady=5)


        # --- Rechte Seite: Staging Area (Bearbeitung) ---
        right_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Ausgewählte Gegner (Anzahl & Werte anpassen)", font=FONTS["large"]).pack(pady=5)

        # Canvas für scrollbare Liste
        self.canvas = tk.Canvas(right_frame, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Header für Staging Area
        self.create_staging_headers()

        self.staging_entries = []

        # Footer Buttons
        btn_frame = ttk.Frame(self.parent, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(btn_frame, text="Alle zum Kampf hinzufügen", command=self.finalize_import).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=self.close_callback).pack(side="right", padx=10)

    def populate_tree(self, data: Dict[str, Any], parent: str = "") -> None:
        """Füllt den Treeview rekursiv mit Kategorien und Gegnern."""
        for key, value in sorted(data.items()):
            if "lp" in value: # Es ist ein Gegner (Blatt)
                self.tree.insert(parent, "end", text=key, values=("enemy",), tags=("enemy",))
            else: # Es ist eine Kategorie
                node = self.tree.insert(parent, "end", text=key, open=False, tags=("category",))
                self.populate_tree(value, node)

    def search(self, query: str) -> int:
        """Führt eine Suche durch und gibt die Anzahl der Treffer zurück."""
        self.search_var.set(query)
        # Check if tree has any children after filtering
        return len(self.tree.get_children())

    def on_search_change(self, *args):
        """Filtert den Baum basierend auf der Sucheingabe."""
        query = self.search_var.get().lower()

        # Baum leeren
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not query:
            self.populate_tree(self.enemy_presets)
            return

        # Gefilterte Daten erstellen
        filtered_data = self._filter_data_recursive(self.enemy_presets, query)
        self.populate_tree(filtered_data)

        # Alle Knoten öffnen, um Ergebnisse zu zeigen
        self._expand_all_nodes()

    def _filter_data_recursive(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        result = {}
        for key, value in data.items():
            if "lp" in value: # Blatt (Gegner)
                if query in key.lower():
                    result[key] = value
            else: # Kategorie
                filtered_children = self._filter_data_recursive(value, query)
                if filtered_children:
                    result[key] = filtered_children
        return result

    def _expand_all_nodes(self, parent=""):
        for item in self.tree.get_children(parent):
            self.tree.item(item, open=True)
            self._expand_all_nodes(item)

    def on_tree_double_click(self, event):
        self.add_selected_to_staging()

    def add_selected_to_staging(self):
        selected_item = self.tree.selection()
        if not selected_item: return

        item_text = self.tree.item(selected_item[0], "text")
        tags = self.tree.item(selected_item[0], "tags")

        if "enemy" in tags:
            if item_text in self.flat_presets:
                data = self.flat_presets[item_text]
                self.add_staging_row(item_text, data)

    def create_staging_headers(self):
        header_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Level", "Anzahl", "Sofort", ""]
        widths = [30, 10, 5, 5, 5, 5, 5, 5, 5, 5]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=FONTS["small"], width=widths[i], anchor="w").pack(side="left", padx=2)

    def add_staging_row(self, name, data):
        row_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        row_frame.pack(fill="x", pady=5)

        # Name
        e_name = ttk.Entry(row_frame, width=30)
        e_name.insert(0, name)
        e_name.pack(side="left", padx=5)

        # Typ
        e_type = ttk.Combobox(row_frame, values=[t.value for t in CharacterType], width=10, state="readonly")
        e_type.set(data.get("type", CharacterType.ENEMY.value))
        e_type.pack(side="left", padx=5)

        # LP
        e_lp = ttk.Entry(row_frame, width=5)
        e_lp.insert(0, str(data.get("lp", 10)))
        e_lp.pack(side="left", padx=5)

        # RP
        e_rp = ttk.Entry(row_frame, width=5)
        e_rp.insert(0, str(data.get("rp", 0)))
        e_rp.pack(side="left", padx=5)

        # SP
        e_sp = ttk.Entry(row_frame, width=5)
        e_sp.insert(0, str(data.get("sp", 0)))
        e_sp.pack(side="left", padx=5)

        # GEW
        e_gew = ttk.Entry(row_frame, width=5)
        e_gew.insert(0, str(data.get("gew", 1)))
        e_gew.pack(side="left", padx=5)

        # Level
        e_level = ttk.Entry(row_frame, width=5)
        e_level.insert(0, str(data.get("level", 0)))
        e_level.pack(side="left", padx=5)

        # Anzahl
        e_count = ttk.Entry(row_frame, width=5)
        e_count.insert(0, "1")
        e_count.pack(side="left", padx=5)

        # Sofort Checkbox
        var_surprise = tk.BooleanVar()
        cb_surprise = ttk.Checkbutton(row_frame, variable=var_surprise)
        cb_surprise.pack(side="left", padx=5)

        # Löschen Button
        btn_del = ttk.Button(row_frame, text="X", width=3)
        btn_del.pack(side="left", padx=5)

        entry_obj = {
            "frame": row_frame,
            "name": e_name,
            "type": e_type,
            "lp": e_lp,
            "rp": e_rp,
            "sp": e_sp,
            "gew": e_gew,
            "level": e_level,
            "count": e_count,
            "surprise": var_surprise
        }

        btn_del.configure(command=lambda: self.remove_staging_row(row_frame, entry_obj))
        self.staging_entries.append(entry_obj)

    def remove_staging_row(self, frame, entry_obj):
        frame.destroy()
        if entry_obj in self.staging_entries:
            self.staging_entries.remove(entry_obj)

    def finalize_import(self):
        """Fügt die konfigurierten Gegner dem Kampf hinzu."""
        count_imported = 0
        self.history_manager.save_snapshot()

        try:
            for entry in self.staging_entries:
                try:
                    count = int(entry["count"].get())
                except ValueError:
                    count = 1

                if count <= 0: continue

                name_base = entry["name"].get()
                char_type = entry["type"].get()
                lp = int(entry["lp"].get())
                rp = int(entry["rp"].get())
                sp = int(entry["sp"].get())
                gew = int(entry["gew"].get())
                if gew > MAX_GEW:
                    gew = MAX_GEW
                level = int(entry["level"].get())
                surprise = entry["surprise"].get()

                for i in range(count):
                    final_name = name_base
                    if count > 1:
                        final_name = f"{name_base} {i+1}"

                    # Init würfeln
                    init = wuerfle_initiative(gew)

                    new_char = Character(final_name, lp, rp, sp, init, gew=gew, char_type=char_type, level=level)
                    self.engine.insert_character(new_char, surprise=surprise)
                    count_imported += 1

            self.engine.log(f"{count_imported} Charaktere aus Bibliothek hinzugefügt.")
            self.close_callback()

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte verwenden.")

    def update_colors(self, colors: Dict[str, str]):
        """Aktualisiert die Farben des Tabs."""
        self.colors = colors
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.configure(bg=self.colors["panel"])
