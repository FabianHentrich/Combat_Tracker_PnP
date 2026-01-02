import tkinter as tk
from tkinter import ttk
from typing import Optional, TYPE_CHECKING, Dict
from src.utils.utils import generate_health_bar

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class CharacterList(ttk.Frame):
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent)
        self.controller = controller
        self.colors = colors
        self.tree = None
        self.context_menu = None

        self._setup_ui()

    def _setup_ui(self):
        columns = ("Order", "Name", "Typ", "LP", "RP", "SP", "GEW", "INIT", "Status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        # Spalten-Definitionen: (Name, Text, Breite, Anchor, Stretch)
        col_defs = [
            ("Order", "#", 30, "center", False),
            ("Name", "Name", 200, "w", True), # minwidth=100 handled separately or default
            ("Typ", "Typ", 80, "center", False),
            ("LP", "LP (Balken)", 200, "center", False),
            ("RP", "RP", 60, "center", False),
            ("SP", "SP", 60, "center", False),
            ("GEW", "GEW", 60, "center", False),
            ("INIT", "INIT", 60, "center", False),
            ("Status", "Status", 700, "w", False) # minwidth=200
        ]

        for col_id, text, width, anchor, stretch in col_defs:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor, stretch=stretch)

        # Spezielle Anpassungen (minwidth)
        self.tree.column("Name", minwidth=100)
        self.tree.column("Status", minwidth=200)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Kontextmenü für Rechtsklick
        self.context_menu = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        self.context_menu.add_command(label="Löschen", command=self.controller.character_handler.delete_character)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.controller.character_handler.on_character_double_click)

    def show_context_menu(self, event: tk.Event) -> None:
        """Zeigt das Kontextmenü bei Rechtsklick auf die Tabelle."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def update_list(self) -> None:
        """
        Aktualisiert die Anzeige der Charakterliste (Treeview).
        """
        tree = self.tree
        if not tree:
            return

        engine = self.controller.engine

        # Treeview leeren
        for item in tree.get_children():
            tree.delete(item)

        if not engine.characters:
            return

        # Rotation berechnen
        rot = 0
        if engine.initiative_rolled and engine.turn_index >= 0:
            if engine.turn_index < len(engine.characters):
                rot = engine.turn_index
            else:
                rot = 0

        # Liste rotieren für Anzeige (Aktiver Char oben)
        n = len(engine.characters)
        display_list = []
        for k in range(n):
            idx = (rot + k) % n
            display_list.append((idx, engine.characters[idx]))

        for orig_idx, char in display_list:
            # Status String holen und Präfix entfernen, da eigene Spalte
            status_str = char.get_status_string().replace(" | Status: ", "")

            order = str(orig_idx + 1) if engine.initiative_rolled else "-"

            # Werte formatieren (Aktuell / Max)
            lp_str = f"{char.lp}/{char.max_lp}"
            rp_str = f"{char.rp}/{char.max_rp}"
            sp_str = f"{char.sp}/{char.max_sp}"

            # Health Bar generieren
            health_bar = generate_health_bar(char.lp, char.max_lp, length=10)

            # Werte einfügen
            item_id = tree.insert("", tk.END, iid=char.id, values=(order, char.name, char.char_type, health_bar, rp_str, sp_str, char.gew, char.init, status_str))

            # Visuelles Feedback für niedrige LP
            tags = []
            if char.lp <= 0 or char.max_lp <= 0:
                tags.append('dead')
            elif char.lp < (char.max_lp * 0.3): # Unter 30% LP
                tags.append('low_hp')

            if tags:
                tree.item(item_id, tags=tuple(tags))

        # Tags für Dark Mode angepasst
        tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
        tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

    def get_selected_id(self) -> Optional[str]:
        selection = self.tree.selection()
        if not selection:
            return None
        return selection[0]

    def highlight(self, char_id: str) -> None:
        if self.tree.exists(char_id):
            self.tree.selection_set(char_id)
            self.tree.focus(char_id)
            self.tree.see(char_id)

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.context_menu:
            self.context_menu.configure(bg=self.colors["panel"], fg=self.colors["fg"])
        if self.tree:
            self.tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
            self.tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

