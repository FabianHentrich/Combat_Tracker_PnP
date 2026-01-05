import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, TYPE_CHECKING, Callable, List
from src.models.enums import DamageType, StatusEffectType, ScopeType
from src.config.rule_manager import rule_manager
from src.utils.utils import ToolTip
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class ActionPanel(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent, text=translate("action_panel.title"), padding="15", style="Card.TLabelframe")
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
        
        # Prepare translated values
        self.translated_damage_types = {translate(f"damage_types.{dt.name}"): dt.value for dt in DamageType}
        self.translated_status_effects = {translate(f"status_effects.{se.name}"): se.value for se in StatusEffectType}
        self.translated_scopes = {
            translate("management_targets.selected"): ScopeType.SELECTED,
            translate("management_targets.all_enemies"): ScopeType.ALL_ENEMIES,
            translate("management_targets.all_players"): ScopeType.ALL_PLAYERS,
            translate("management_targets.all_npcs"): ScopeType.ALL_NPCS,
            translate("management_targets.all_characters"): ScopeType.ALL
        }

        self._setup_ui()

    def _setup_ui(self):
        # --- Damage Section (Dynamic) ---
        ttk.Label(self, text=translate("action_panel.damage_healing_label")).pack(anchor="w")
        
        # Container for dynamic rows
        self.rows_frame = ttk.Frame(self)
        self.rows_frame.pack(fill="x", pady=(0, 5))
        
        # Add the first row initially
        self.add_damage_row()
        
        # Buttons for row management
        row_btn_frame = ttk.Frame(self)
        row_btn_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(row_btn_frame, text="+", width=3, command=self.add_damage_row).pack(side="left")
        
        # Total display
        self.lbl_total = ttk.Label(row_btn_frame, text=f"{translate('action_panel.total')}: 0", font=("Arial", 9, "bold"))
        self.lbl_total.pack(side="right", padx=5)

        # Action buttons grid
        btn_grid = ttk.Frame(self, style="Card.TFrame")
        btn_grid.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_grid, text=translate("action_panel.deal_damage_btn"), command=self.controller.combat_handler.deal_damage).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text=translate("action_panel.heal_btn"), command=self.controller.combat_handler.apply_healing).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text=translate("action_panel.add_shield_btn"), command=self.controller.combat_handler.apply_shield).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text=translate("action_panel.add_armor_btn"), command=self.controller.combat_handler.apply_armor).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # --- Status Section (Inline) ---
        ttk.Label(self, text=translate("action_panel.status_effect_label")).pack(anchor="w")

        status_frame = ttk.Frame(self, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.status_combobox = ttk.Combobox(status_frame, values=list(self.translated_status_effects.keys()), state="readonly")
        self.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        if self.translated_status_effects:
            self.status_combobox.set(list(self.translated_status_effects.keys())[0])

        self.create_tooltip(self.status_combobox, lambda: f"{self.status_combobox.get()}:\n{rule_manager.status_effect_descriptions.get(self.translated_status_effects.get(self.status_combobox.get()), translate('messages.no_info'))}")

        rank_duration_frame = ttk.Frame(self, style="Card.TFrame")
        rank_duration_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rank_duration_frame, text=f"{translate('action_panel.rank')}:").pack(side=tk.LEFT)
        self.status_rank = ttk.Entry(rank_duration_frame, width=5)
        self.status_rank.pack(side=tk.LEFT, padx=(5, 15))
        self.status_rank.insert(0, "1")

        ttk.Label(rank_duration_frame, text=f"{translate('action_panel.duration')}:").pack(side=tk.LEFT)
        self.status_duration = ttk.Entry(rank_duration_frame, width=5)
        self.status_duration.pack(side=tk.LEFT, padx=(5, 0))
        self.status_duration.insert(0, "3")

        ttk.Button(self, text=translate("action_panel.add_status_btn"), command=self.controller.combat_handler.add_status_to_character).pack(fill=tk.X, pady=2)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Management Section
        ttk.Label(self, text=translate("action_panel.management_label")).pack(anchor="w")

        self.management_target_var = tk.StringVar(value=translate("management_targets.selected"))
        target_cb = ttk.Combobox(self, textvariable=self.management_target_var,
                                 values=list(self.translated_scopes.keys()),
                                 state="readonly")
        target_cb.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(self, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        self.btn_edit = ttk.Button(btn_frame, text=translate("common.edit"), command=self.controller.character_handler.manage_edit)
        self.btn_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        ttk.Button(btn_frame, text=translate("common.delete"), command=self.controller.character_handler.manage_delete).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        def update_edit_state(event):
            if self.management_target_var.get() == translate("management_targets.selected"):
                self.btn_edit.state(["!disabled"])
            else:
                self.btn_edit.state(["disabled"])

        target_cb.bind("<<ComboboxSelected>>", update_edit_state)

    def add_damage_row(self):
        row_frame = ttk.Frame(self.rows_frame)
        row_frame.pack(fill="x", pady=2)
        
        # Input field for amount
        amount_var = tk.StringVar(value="0")
        amount_var.trace_add("write", self.calculate_total)
        entry = ttk.Entry(row_frame, textvariable=amount_var, width=6, font=("Arial", 12, "bold"), justify="center")
        entry.pack(side="left", padx=(0, 5))
        
        # Dropdown for type
        type_var = tk.StringVar(value=list(self.translated_damage_types.keys())[0] if self.translated_damage_types else "")
        combo = ttk.Combobox(row_frame, textvariable=type_var, values=list(self.translated_damage_types.keys()), state="readonly")
        self.create_tooltip(combo, lambda: f"{type_var.get()}:\n{rule_manager.damage_type_descriptions.get(self.translated_damage_types.get(type_var.get()), translate('messages.no_info'))}")
        combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Delete button (only if not the first row)
        if len(self.damage_rows) > 0:
            btn_del = ttk.Button(row_frame, text="x", width=2, command=lambda: self.remove_damage_row(row_frame))
            btn_del.pack(side="left")
        
        self.damage_rows.append({
            "frame": row_frame,
            "amount": amount_var,
            "type": type_var,
            "entry": entry
        })
        
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
            self.lbl_total.config(text=f"{translate('action_panel.total')}: {total}")
        return total

    def create_tooltip(self, widget: tk.Widget, text_func: Callable[[], str]) -> None:
        tt = ToolTip(widget, text_func, color_provider=lambda: (self.colors["tooltip_bg"], self.colors["tooltip_fg"]))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def focus_value_input(self) -> None:
        if self.damage_rows:
            self.damage_rows[0]["entry"].focus_set()

    def get_damage_data(self) -> tuple[int, str]:
        """Returns (total_damage, detail_string)."""
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

    def get_value(self) -> int:
        return self.calculate_total()

    def get_type(self) -> str:
        if self.damage_rows:
            display_name = self.damage_rows[0]["type"].get()
            return self.translated_damage_types.get(display_name, DamageType.NORMAL.value)
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

        display_name = self.status_combobox.get()
        status_value = self.translated_status_effects.get(display_name, StatusEffectType.POISON.value)

        return {
            "status": status_value,
            "rank": rank,
            "duration": duration
        }

    def get_management_target(self) -> ScopeType:
        display_value = self.management_target_var.get()
        return self.translated_scopes.get(display_value, ScopeType.SELECTED)

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
