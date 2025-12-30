import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, TYPE_CHECKING
from .character import Character
from .utils import wuerfle_initiative
from .logger import setup_logging

if TYPE_CHECKING:
    from .main_window import CombatTracker

logger = setup_logging()

class LibraryHandler:
    def __init__(self, tracker: 'CombatTracker', root: tk.Tk, colors: Dict[str, str]):
        self.tracker = tracker
        self.root = root
        self.colors = colors
        self.staging_entries: List[Dict[str, Any]] = []

    def open_library_window(self) -> None:
        """Öffnet das Bibliotheks-Fenster."""
        lib_window = tk.Toplevel(self.root)
        lib_window.title("Gegner-Bibliothek")
        lib_window.geometry("1200x900")
        lib_window.configure(bg=self.colors["bg"])

        # Layout: Links Baumstruktur (Auswahl), Rechts Liste (Bearbeitung/Anzahl)
        paned = ttk.PanedWindow(lib_window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Linke Seite: Auswahl ---
        left_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Verfügbare Gegner", font=('Segoe UI', 12, 'bold'), background=self.colors["panel"]).pack(pady=5)

        # Treeview für Kategorien
        self.tree = ttk.Treeview(left_frame, selectmode="browse", show="tree headings")
        self.tree.heading("#0", text="Kategorie / Name", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar für Treeview
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y") # Pack scrollbar next to tree? No, pack layout is tricky here.
        # Better layout for scrollbar
        self.tree.pack_forget()
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if not self.tracker.enemy_presets_structure:
            self.tree.insert("", "end", text="Keine Gegner gefunden (enemies.json prüfen)", tags=("error",))
            logger.warning("Keine Gegner-Presets gefunden.")
        else:
            try:
                self.populate_tree(self.tracker.enemy_presets_structure)
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

        ttk.Label(right_frame, text="Ausgewählte Gegner (Anzahl & Werte anpassen)", font=('Segoe UI', 12, 'bold'), background=self.colors["panel"]).pack(pady=5)

        # Canvas für scrollbare Liste
        canvas = tk.Canvas(right_frame, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Header für Staging Area
        self.create_staging_headers()

        self.staging_entries = []

        # Footer Buttons
        btn_frame = ttk.Frame(lib_window, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(btn_frame, text="Alle zum Kampf hinzufügen", command=lambda: self.finalize_import(lib_window)).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=lib_window.destroy).pack(side="right", padx=10)

    def populate_tree(self, data: Dict[str, Any], parent: str = "") -> None:
        """Füllt den Treeview rekursiv mit Kategorien und Gegnern."""
        for key, value in data.items():
            if "lp" in value: # Es ist ein Gegner (Blatt)
                # Wir speichern die Stats direkt im Item als Values oder Tags, oder holen sie später aus self.tracker.enemy_presets
                self.tree.insert(parent, "end", text=key, values=("enemy",), tags=("enemy",))
            else: # Es ist eine Kategorie
                node = self.tree.insert(parent, "end", text=key, open=False, tags=("category",))
                self.populate_tree(value, node)

    def on_tree_double_click(self, event):
        self.add_selected_to_staging()

    def add_selected_to_staging(self):
        selected_item = self.tree.selection()
        if not selected_item: return

        item_text = self.tree.item(selected_item[0], "text")
        tags = self.tree.item(selected_item[0], "tags")

        if "enemy" in tags:
            # Daten holen (wir nutzen das flache Dictionary im Tracker für einfachen Zugriff)
            if item_text in self.tracker.enemy_presets:
                data = self.tracker.enemy_presets[item_text]
                self.add_staging_row(item_text, data)

    def create_staging_headers(self):
        header_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Anzahl", "Sofort", ""]
        widths = [30, 10, 5, 5, 5, 5, 5.5, 5, 10]

        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=('Segoe UI', 9, 'bold'), width=widths[i], anchor="w", background=self.colors["panel"]).pack(side="left", padx=2)

    def add_staging_row(self, name, data):
        row_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        row_frame.pack(fill="x", pady=5)

        # Name
        e_name = ttk.Entry(row_frame, width=30)
        e_name.insert(0, name)
        e_name.pack(side="left", padx=5)

        # Typ
        e_type = ttk.Combobox(row_frame, values=["Spieler", "Gegner", "NPC"], width=10, state="readonly")
        e_type.set(data.get("type", "Gegner"))
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
            "count": e_count,
            "surprise": var_surprise
        }

        btn_del.configure(command=lambda: self.remove_staging_row(row_frame, entry_obj))
        self.staging_entries.append(entry_obj)

    def remove_staging_row(self, frame, entry_obj):
        frame.destroy()
        if entry_obj in self.staging_entries:
            self.staging_entries.remove(entry_obj)

    def finalize_import(self, window):
        """Fügt die konfigurierten Gegner dem Kampf hinzu."""
        count_imported = 0
        self.tracker.history_manager.save_snapshot()

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
                surprise = entry["surprise"].get()

                for i in range(count):
                    final_name = name_base
                    if count > 1:
                        final_name = f"{name_base} {i+1}"

                    # Init würfeln
                    init = wuerfle_initiative(gew)

                    new_char = Character(final_name, lp, rp, sp, init, gew=gew, char_type=char_type)
                    self.tracker.insert_character(new_char, surprise=surprise)
                    count_imported += 1

            self.tracker.update_listbox()
            self.tracker.log_message(f"{count_imported} Charaktere aus Bibliothek hinzugefügt.")
            window.destroy()

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte verwenden.")
