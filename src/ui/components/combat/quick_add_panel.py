import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING
from src.models.enums import CharacterType
from src.config.defaults import DEFAULT_GEW

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class QuickAddPanel(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker'):
        super().__init__(parent, text="Neuen Charakter hinzufügen", padding="15", style="Card.TLabelframe")
        self.controller = controller

        self.entry_name = None
        self.entry_lp = None
        self.entry_rp = None
        self.entry_sp = None
        self.entry_init = None
        self.entry_gew = None
        self.entry_level = None
        self.entry_type = None
        self.var_surprise = None

        self._setup_ui()

    def _setup_ui(self):
        # Zeile 0: Bibliothek (Button) und Excel Import
        ttk.Button(self, text="📚 Bibliothek öffnen...", command=self.controller.library_handler.open_library_window).grid(row=0, column=0, columnspan=2, padx=5, sticky="ew")
        ttk.Button(self, text="Excel Import", command=lambda: self.controller.import_handler.load_from_excel(None)).grid(row=0, column=2, columnspan=2, padx=5, sticky="ew")

        # Zeile 1: Eingabefelder
        col = 0
        self.entry_name = self._create_entry("Name:", col, width=20)
        col += 2
        self.entry_lp = self._create_entry("LP:", col, width=8)
        col += 2
        self.entry_rp = self._create_entry("RP:", col, width=8)
        col += 2
        self.entry_sp = self._create_entry("SP:", col, width=8)
        col += 2
        self.entry_init = self._create_entry("INIT:", col, width=8)
        col += 2
        self.entry_gew = self._create_entry("GEW:", col, width=8)
        self.entry_gew.insert(0, str(DEFAULT_GEW))
        col += 2
        self.entry_level = self._create_entry("Level:", col, width=8)
        self.entry_level.insert(0, "0")
        col += 2

        ttk.Label(self, text="Typ:").grid(row=1, column=col, padx=5, sticky="w")
        self.entry_type = ttk.Combobox(self, values=[t.value for t in CharacterType], width=10, state="readonly")
        self.entry_type.set(CharacterType.ENEMY.value)
        self.entry_type.grid(row=1, column=col+1, padx=5)
        col += 2

        # Checkbox für "Sofort agieren"
        self.var_surprise = tk.BooleanVar()
        ttk.Checkbutton(self, text="Sofort dran", variable=self.var_surprise).grid(row=1, column=col, padx=5)
        col += 1

        ttk.Button(self, text="Hinzufügen", command=self.controller.character_handler.add_character_quick).grid(row=1, column=col, padx=10)

    def _create_entry(self, label_text, col, width=10):
        ttk.Label(self, text=label_text).grid(row=1, column=col, padx=5, sticky="w")
        entry = ttk.Entry(self, width=width)
        entry.grid(row=1, column=col+1, padx=5)
        return entry

    def get_data(self) -> Dict[str, Any]:
        return {
            "name": self.entry_name.get(),
            "lp": self.entry_lp.get(),
            "rp": self.entry_rp.get(),
            "sp": self.entry_sp.get(),
            "init": self.entry_init.get(),
            "gew": self.entry_gew.get(),
            "level": self.entry_level.get(),
            "type": self.entry_type.get(),
            "surprise": self.var_surprise.get()
        }

    def clear(self) -> None:
        self.entry_name.delete(0, tk.END)
        self.entry_lp.delete(0, tk.END)
        self.entry_rp.delete(0, tk.END)
        self.entry_sp.delete(0, tk.END)
        self.entry_init.delete(0, tk.END)
        self.entry_gew.delete(0, tk.END)
        self.entry_level.delete(0, tk.END)
        self.entry_name.focus()
        self.var_surprise.set(False)

    def set_defaults(self) -> None:
        self.var_surprise.set(False)
        self.entry_gew.delete(0, tk.END)
        self.entry_gew.insert(0, str(DEFAULT_GEW))
        self.entry_level.delete(0, tk.END)
        self.entry_level.insert(0, "0")

    def fill_fields(self, data: Dict[str, Any]) -> None:
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, data.get("name", ""))

        self.entry_lp.delete(0, tk.END)
        self.entry_lp.insert(0, str(data.get("lp", 10)))

        self.entry_rp.delete(0, tk.END)
        self.entry_rp.insert(0, str(data.get("rp", 0)))

        self.entry_sp.delete(0, tk.END)
        self.entry_sp.insert(0, str(data.get("sp", 0)))

        self.entry_gew.delete(0, tk.END)
        self.entry_gew.insert(0, str(data.get("gew", 1)))

        self.entry_init.delete(0, tk.END)
        self.entry_init.insert(0, str(data.get("init", 0)))

        self.entry_level.delete(0, tk.END)
        self.entry_level.insert(0, str(data.get("level", 0)))

        self.entry_type.set(data.get("type", CharacterType.ENEMY.value))
