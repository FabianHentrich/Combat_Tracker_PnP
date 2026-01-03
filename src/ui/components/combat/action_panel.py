import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING, Callable, List
from src.models.enums import DamageType, StatusEffectType
from src.config import FONTS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, DEFAULT_RULES
from src.utils.utils import ToolTip

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class ActionPanel(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent, text="Interaktion", padding="15", style="Card.TLabelframe")
        self.controller = controller
        self.colors = colors

        self.damage_rows = []
        self.rows_frame = None
        self.lbl_total = None
        
        self.status_combobox = None
        self.status_rank = None
        self.status_duration = None
        self.management_target_var = None
        self.btn_edit = None
        
        # Schadenstypen aus DEFAULT_RULES laden
        self.damage_types = list(DEFAULT_RULES["damage_types"].keys())

        self._setup_ui()

    def _setup_ui(self):
        # --- Schaden Sektion (Dynamisch) ---
        ttk.Label(self, text="Schaden / Heilung:").pack(anchor="w")
        
        # Container für die dynamischen Zeilen
        self.rows_frame = ttk.Frame(self)
        self.rows_frame.pack(fill="x", pady=(0, 5))
        
        # Erste Zeile initial hinzufügen
        self.add_damage_row()
        
        # Buttons für Zeilen-Management
        row_btn_frame = ttk.Frame(self)
        row_btn_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(row_btn_frame, text="+", width=3, command=self.add_damage_row).pack(side="left")
        
        # Summen-Anzeige
        self.lbl_total = ttk.Label(row_btn_frame, text="Gesamt: 0", font=("Arial", 9, "bold"))
        self.lbl_total.pack(side="right", padx=5)

        # Aktions-Buttons Grid
        btn_grid = ttk.Frame(self, style="Card.TFrame")
        btn_grid.pack(fill=tk.X, pady=(5, 0))

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

    def add_damage_row(self):
        row_frame = ttk.Frame(self.rows_frame)
        row_frame.pack(fill="x", pady=2)
        
        # Eingabefeld für Menge
        amount_var = tk.StringVar(value="0")
        amount_var.trace_add("write", self.calculate_total)
        entry = ttk.Entry(row_frame, textvariable=amount_var, width=6, font=FONTS["large"], justify="center")
        entry.pack(side="left", padx=(0, 5))
        
        # Dropdown für Typ
        type_var = tk.StringVar(value=self.damage_types[0] if self.damage_types else "")
        combo = ttk.Combobox(row_frame, textvariable=type_var, values=self.damage_types, state="readonly")
        combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Löschen Button (nur wenn nicht die erste Zeile)
        if len(self.damage_rows) > 0:
            btn_del = ttk.Button(row_frame, text="x", width=2, command=lambda: self.remove_damage_row(row_frame))
            btn_del.pack(side="left")
        
        self.damage_rows.append({
            "frame": row_frame,
            "amount": amount_var,
            "type": type_var,
            "entry": entry
        })
        
        # Fokus auf das neue Feld setzen (optional, aber praktisch)
        # entry.focus_set()
        # entry.select_range(0, tk.END)

    def remove_damage_row(self, frame):
        self.damage_rows = [r for r in self.damage_rows if r["frame"] != frame]
        frame.destroy()
        self.calculate_total()

    def calculate_total(self, *args):
        total = 0
        for row in self.damage_rows:
            try:
                val = int(row["amount"].get())
                total += val
            except ValueError:
                pass
        if self.lbl_total:
            self.lbl_total.config(text=f"Gesamt: {total}")
        return total

    def create_tooltip(self, widget: tk.Widget, text_func: Callable[[], str]) -> None:
        tt = ToolTip(widget, text_func, color_provider=lambda: (self.colors["tooltip_bg"], self.colors["tooltip_fg"]))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def focus_value_input(self) -> None:
        if self.damage_rows:
            self.damage_rows[0]["entry"].focus_set()

    def get_damage_data(self) -> tuple[int, str]:
        """Gibt (Gesamtschaden, Detail-String) zurück."""
        total = self.calculate_total()
        details = []
        
        for row in self.damage_rows:
            try:
                val = int(row["amount"].get())
                if val > 0:
                    t = row["type"].get()
                    details.append(f"{val} {t}")
            except ValueError:
                pass
        
        detail_str = ", ".join(details) if details else "0 Normal"
        return total, detail_str

    # Kompatibilitäts-Methoden für bestehenden Code (falls nötig)
    def get_value(self) -> int:
        return self.calculate_total()

    def get_type(self) -> str:
        # Gibt den Typ der ersten Zeile zurück oder "Normal"
        if self.damage_rows:
            return self.damage_rows[0]["type"].get()
        return DamageType.NORMAL.value

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
