import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING, Callable
from src.models.enums import DamageType, StatusEffectType
from src.config import FONTS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS
from src.utils.utils import ToolTip

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class ActionPanel(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent, text="Interaktion", padding="15", style="Card.TLabelframe")
        self.controller = controller
        self.colors = colors

        self.action_value = None
        self.action_type = None
        self.status_combobox = None
        self.status_rank = None
        self.status_duration = None
        self.management_target_var = None
        self.btn_edit = None

        self._setup_ui()

    def _setup_ui(self):
        # Wert Eingabe (Groß)
        ttk.Label(self, text="Wert:").pack(anchor="w")
        self.action_value = ttk.Entry(self, font=FONTS["xl"], justify="center")
        self.action_value.pack(fill=tk.X, pady=(0, 10))
        self.action_value.insert(0, "0")

        # Typ Auswahl
        ttk.Label(self, text="Typ:").pack(anchor="w")
        self.action_type = ttk.Combobox(self, values=[t.value for t in DamageType], state="readonly")
        self.action_type.set(DamageType.NORMAL.value)
        self.action_type.pack(fill=tk.X, pady=(0, 15))

        self.create_tooltip(self.action_type, lambda: DAMAGE_DESCRIPTIONS.get(self.action_type.get(), ""))

        # Aktions-Buttons Grid
        btn_grid = ttk.Frame(self, style="Card.TFrame")
        btn_grid.pack(fill=tk.X)

        ttk.Button(btn_grid, text="⚔️ Schaden", command=self.controller.combat_handler.deal_damage).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="💚 Heilen", command=self.controller.combat_handler.apply_healing).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="🛡️ Schild +", command=self.controller.combat_handler.apply_shield).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="👕 Rüstung +", command=self.controller.combat_handler.apply_armor).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # --- Status Sektion (Inline) ---
        ttk.Label(self, text="Status Effekt:").pack(anchor="w")

        status_frame = ttk.Frame(self, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.status_combobox = ttk.Combobox(status_frame, values=[t.value for t in StatusEffectType], state="readonly")
        self.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.status_combobox.set(StatusEffectType.POISON.value)

        self.create_tooltip(self.status_combobox, lambda: f"{self.status_combobox.get()}:\n{STATUS_DESCRIPTIONS.get(self.status_combobox.get(), 'Keine Info')}")

        rank_duration_frame = ttk.Frame(self, style="Card.TFrame")
        rank_duration_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rank_duration_frame, text="Rang:").pack(side=tk.LEFT)
        self.status_rank = ttk.Entry(rank_duration_frame, width=5)
        self.status_rank.pack(side=tk.LEFT, padx=(5, 15))
        self.status_rank.insert(0, "1")

        ttk.Label(rank_duration_frame, text="Dauer:").pack(side=tk.LEFT)
        self.status_duration = ttk.Entry(rank_duration_frame, width=5)
        self.status_duration.pack(side=tk.LEFT, padx=(5, 0))
        self.status_duration.insert(0, "3")

        ttk.Button(self, text="Status hinzufügen", command=self.controller.combat_handler.add_status_to_character).pack(fill=tk.X, pady=2)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Management Section
        ttk.Label(self, text="Verwaltung:").pack(anchor="w")

        self.management_target_var = tk.StringVar(value="Ausgewählter Charakter")
        target_cb = ttk.Combobox(self, textvariable=self.management_target_var,
                                 values=["Ausgewählter Charakter", "Alle Gegner", "Alle Spieler", "Alle NPCs", "Alle Charaktere"],
                                 state="readonly")
        target_cb.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(self, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        self.btn_edit = ttk.Button(btn_frame, text="Bearbeiten", command=self.controller.character_handler.manage_edit)
        self.btn_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        ttk.Button(btn_frame, text="Löschen", command=self.controller.character_handler.manage_delete).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        def update_edit_state(event):
            if self.management_target_var.get() == "Ausgewählter Charakter":
                self.btn_edit.state(["!disabled"])
            else:
                self.btn_edit.state(["disabled"])

        target_cb.bind("<<ComboboxSelected>>", update_edit_state)

    def create_tooltip(self, widget: tk.Widget, text_func: Callable[[], str]) -> None:
        tt = ToolTip(widget, text_func, color_provider=lambda: (self.colors["tooltip_bg"], self.colors["tooltip_fg"]))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def focus_value_input(self) -> None:
        if self.action_value:
            self.action_value.focus_set()

    def get_value(self) -> int:
        try:
            val = self.action_value.get()
            return int(val) if val else 0
        except ValueError:
            return 0

    def get_type(self) -> str:
        return self.action_type.get()

    def get_status_input(self) -> Dict[str, Any]:
        try:
            rank = int(self.status_rank.get())
        except ValueError:
            rank = 1

        try:
            duration = int(self.status_duration.get())
        except ValueError:
            duration = 3

        return {
            "status": self.status_combobox.get(),
            "rank": rank,
            "duration": duration
        }

    def get_management_target(self) -> str:
        return self.management_target_var.get()

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors

