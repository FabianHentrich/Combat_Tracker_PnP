import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, TYPE_CHECKING
from src.models.enums import EventType
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker


class TurnBanner(ttk.Frame):
    """
    Zeigt aktuelle Runde, aktiven Charakter mit HP-Balken und Status oben im Kampfbereich.
    """
    _HP_BAR_W = 160
    _HP_BAR_H = 14

    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent, style="Card.TFrame", padding=(10, 6))
        self.controller = controller
        self.colors = colors

        self._canvas: Optional[tk.Canvas] = None
        self._lbl_round: Optional[ttk.Label] = None
        self._lbl_name: Optional[ttk.Label] = None
        self._lbl_lp: Optional[ttk.Label] = None
        self._lbl_status: Optional[ttk.Label] = None

        self._setup_ui()

        engine = controller.engine
        engine.subscribe(EventType.UPDATE, lambda: self.refresh())
        engine.subscribe(EventType.TURN_CHANGE, lambda: self.refresh())

    def _setup_ui(self):
        self.columnconfigure(0, weight=0)  # Round label
        self.columnconfigure(1, weight=1)  # Character info
        self.columnconfigure(2, weight=0)  # Next Turn button

        # Left: Round label
        self._lbl_round = ttk.Label(self, text="", font=("Arial", 11, "bold"))
        self._lbl_round.grid(row=0, column=0, rowspan=2, padx=(0, 18), sticky="w")

        # Middle: Name + HP bar + status
        info_frame = ttk.Frame(self, style="Card.TFrame")
        info_frame.grid(row=0, column=1, rowspan=2, sticky="ew")

        name_hp_frame = ttk.Frame(info_frame, style="Card.TFrame")
        name_hp_frame.pack(fill="x")

        self._lbl_name = ttk.Label(name_hp_frame, text="", font=("Arial", 11, "bold"))
        self._lbl_name.pack(side="left", padx=(0, 10))

        self._canvas = tk.Canvas(
            name_hp_frame,
            width=self._HP_BAR_W,
            height=self._HP_BAR_H,
            highlightthickness=1,
            highlightbackground=self.colors.get("border", "#555"),
        )
        self._canvas.pack(side="left", padx=(0, 8))

        self._lbl_lp = ttk.Label(name_hp_frame, text="", font=("Arial", 9))
        self._lbl_lp.pack(side="left")

        self._lbl_status = ttk.Label(
            info_frame, text="", font=("Arial", 9), wraplength=500, justify="left"
        )
        self._lbl_status.pack(fill="x", pady=(2, 0))

        # Right: Next Turn button (prominent)
        btn = ttk.Button(
            self,
            text=translate("bottom_panel.next_turn_btn"),
            command=self.controller.combat_handler.next_turn,
        )
        btn.grid(row=0, column=2, rowspan=2, padx=(18, 0), sticky="e", ipadx=12, ipady=5)

    def refresh(self):
        engine = self.controller.engine
        self._lbl_round.config(text=f"{translate('main_view.round')} {engine.round_number}")

        if not engine.initiative_rolled or not engine.characters:
            self._lbl_name.config(text=translate("turn_banner.no_initiative"))
            self._lbl_lp.config(text="")
            self._lbl_status.config(text="")
            self._draw_hp_bar(0, 1)
            return

        idx = engine.turn_index % len(engine.characters)
        char = engine.characters[idx]
        self._lbl_name.config(text=char.name)
        self._lbl_lp.config(text=f"LP: {char.lp}/{char.max_lp}")
        status_str = char.get_status_string().replace(" | Status: ", "").strip()
        self._lbl_status.config(text=status_str)
        self._draw_hp_bar(char.lp, char.max_lp)

    def _draw_hp_bar(self, lp: int, max_lp: int):
        c = self._canvas
        c.delete("all")
        w, h = self._HP_BAR_W, self._HP_BAR_H
        ratio = max(0.0, min(1.0, lp / max_lp)) if max_lp > 0 else 0.0

        bg = self.colors.get("entry_bg", "#333")
        if ratio > 0.5:
            fill = "#4caf50"
        elif ratio > 0.25:
            fill = "#ff9800"
        else:
            fill = "#f44336"

        c.configure(bg=bg)
        c.create_rectangle(0, 0, int(w * ratio), h, fill=fill, outline="")

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self._canvas and self._canvas.winfo_exists():
            self._canvas.configure(
                highlightbackground=colors.get("border", "#555")
            )
        self.refresh()
