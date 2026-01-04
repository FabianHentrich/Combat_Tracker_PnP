import tkinter as tk
from tkinter import ttk
from typing import Optional, TYPE_CHECKING, Dict, List
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
        columns = ("Order", "Name", "Typ", "Level", "LP", "RP", "SP", "GEW", "INIT", "Status")
        # selectmode="extended" ermöglicht die Mehrfachauswahl
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="extended")

        # Spalten-Definitionen
        col_defs = [
            ("Order", "#", 30, "center", False),
            ("Name", "Name", 200, "w", True),
            ("Typ", "Typ", 80, "center", False),
            ("Level", "Level", 50, "center", False),
            ("LP", "LP (Balken)", 200, "center", False),
            ("RP", "RP", 60, "center", False),
            ("SP", "SP", 60, "center", False),
            ("GEW", "GEW", 60, "center", False),
            ("INIT", "INIT", 60, "center", False),
            ("Status", "Status", 700, "w", False)
        ]

        for col_id, text, width, anchor, stretch in col_defs:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor, stretch=stretch)

        self.tree.column("Name", minwidth=100)
        self.tree.column("Status", minwidth=200)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.context_menu = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        self.context_menu.add_command(label="Löschen", command=self.controller.character_handler.delete_character)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.controller.character_handler.on_character_double_click)

    def show_context_menu(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            # Wenn das angeklickte Item nicht bereits Teil der Auswahl ist,
            # wird die Auswahl auf dieses eine Item zurückgesetzt.
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def update_list(self) -> None:
        tree = self.tree
        if not tree: return

        engine = self.controller.engine
        for item in tree.get_children():
            tree.delete(item)

        if not engine.characters: return

        rot = 0
        if engine.initiative_rolled and engine.turn_index >= 0:
            rot = min(engine.turn_index, len(engine.characters) - 1)

        n = len(engine.characters)
        display_list = [( (rot + k) % n, engine.characters[(rot + k) % n] ) for k in range(n)]

        for orig_idx, char in display_list:
            status_str = char.get_status_string().replace(" | Status: ", "")
            order = str(orig_idx + 1) if engine.initiative_rolled else "-"
            lp_str = f"{char.lp}/{char.max_lp}"
            rp_str = f"{char.rp}/{char.max_rp}"
            sp_str = f"{char.sp}/{char.max_sp}"
            health_bar = generate_health_bar(char.lp, char.max_lp, length=10)

            item_id = tree.insert("", tk.END, iid=char.id, values=(order, char.name, char.char_type, char.level, health_bar, rp_str, sp_str, char.gew, char.init, status_str))

            tags = []
            if char.lp <= 0 or char.max_lp <= 0:
                tags.append('dead')
            elif char.lp < (char.max_lp * 0.3):
                tags.append('low_hp')

            if tags:
                tree.item(item_id, tags=tuple(tags))

        tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
        tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

    def get_selected_id(self) -> Optional[str]:
        """Gibt die ID des ERSTEN ausgewählten Items zurück (für Abwärtskompatibilität)."""
        selection = self.tree.selection()
        return selection[0] if selection else None

    def get_selected_ids(self) -> List[str]:
        """Gibt eine Liste aller ausgewählten Item-IDs zurück."""
        return list(self.tree.selection())

    def highlight(self, char_id: str) -> None:
        if self.tree.exists(char_id):
            self.tree.selection_set(char_id)
            self.tree.focus(char_id)
            self.tree.see(char_id)

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.context_menu and self.context_menu.winfo_exists():
            self.context_menu.configure(bg=self.colors["panel"], fg=self.colors["fg"])
        if self.tree and self.tree.winfo_exists():
            self.tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
            self.tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])
