import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, TYPE_CHECKING
from src.config import FONTS
from src.models.enums import CharacterType, ScopeType
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker


class ControlBar(ttk.Frame):
    """
    Always-visible bar above the notebook tabs.
    Row 0: combat controls (initiative, next turn, reset, undo, redo, round label)
    Row 1: QuickAdd panel
    """

    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent, padding=(8, 5))
        self.controller = controller
        self.colors = colors
        self.round_label: Optional[ttk.Label] = None
        self._reset_menu: Optional[tk.Menu] = None

        self.columnconfigure(0, weight=1)
        self._setup_ui()

    def _setup_ui(self):
        from src.ui.components.combat.quick_add_panel import QuickAddPanel

        # --- Row 0: Combat controls ---
        ctrl = ttk.Frame(self)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        ttk.Button(
            ctrl, text=translate("bottom_panel.roll_initiative_btn"),
            command=self.controller.combat_handler.roll_initiative_all,
        ).pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(
            ctrl, text=translate("bottom_panel.next_turn_btn"),
            command=self.controller.combat_handler.next_turn,
        ).pack(side=tk.LEFT, padx=(0, 4))

        reset_btn = ttk.Menubutton(ctrl, text=translate("bottom_panel.reset_initiative_btn"))
        self._reset_menu = tk.Menu(
            reset_btn, tearoff=0,
            bg=self.colors["panel"], fg=self.colors["fg"],
        )
        self._reset_menu.add_command(
            label=translate("bottom_panel.reset_options.all"),
            command=lambda: self.controller.combat_handler.reset_initiative(ScopeType.ALL.value),
        )
        self._reset_menu.add_command(
            label=translate("bottom_panel.reset_options.enemies"),
            command=lambda: self.controller.combat_handler.reset_initiative(CharacterType.ENEMY.value),
        )
        self._reset_menu.add_command(
            label=translate("bottom_panel.reset_options.players"),
            command=lambda: self.controller.combat_handler.reset_initiative(CharacterType.PLAYER.value),
        )
        self._reset_menu.add_command(
            label=translate("bottom_panel.reset_options.npcs"),
            command=lambda: self.controller.combat_handler.reset_initiative(CharacterType.NPC.value),
        )
        reset_btn.config(menu=self._reset_menu)
        reset_btn.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            ctrl, text=translate("bottom_panel.undo_btn"),
            command=self.controller.history_manager.undo,
        ).pack(side=tk.LEFT, padx=(0, 2))

        ttk.Button(
            ctrl, text=translate("bottom_panel.redo_btn"),
            command=self.controller.history_manager.redo,
        ).pack(side=tk.LEFT, padx=(0, 0))

        self.round_label = ttk.Label(
            ctrl,
            text=f"{translate('main_view.round')}: 1",
            font=FONTS["large"],
        )
        self.round_label.pack(side=tk.RIGHT, padx=(0, 4))

        # --- Row 1: QuickAdd ---
        self.quick_add = QuickAddPanel(self, self.controller)
        self.quick_add.grid(row=1, column=0, sticky="ew")

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.round_label and self.round_label.winfo_exists():
            self.round_label.configure(foreground=colors.get("fg", ""))
        if self._reset_menu:
            try:
                self._reset_menu.configure(bg=colors["panel"], fg=colors["fg"])
            except tk.TclError:
                pass
