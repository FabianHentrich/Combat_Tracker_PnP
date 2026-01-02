import tkinter as tk
from tkinter import ttk
from typing import Dict, TYPE_CHECKING, Optional
from src.config import FONTS
from src.ui.components.dice_roller import DiceRoller

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class BottomPanel(ttk.Frame):
    """
    Panel für den unteren Bereich des Hauptfensters.
    Enthält Kampfsteuerung, Log und Würfel-Simulator.
    """
    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent)
        self.controller = controller
        self.colors = colors

        self.round_label: Optional[ttk.Label] = None
        self.log: Optional[tk.Text] = None
        self.dice_roller: Optional[DiceRoller] = None

        self._setup_ui()

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True, pady=5)

        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Button(control_frame, text="🎲 Initiative würfeln & sortieren", command=self.controller.combat_handler.roll_initiative_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏭ Nächster Zug", command=self.controller.combat_handler.next_turn).pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Menubutton(control_frame, text="🔄 Init Reset")
        reset_menu = tk.Menu(reset_btn, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        reset_menu.add_command(label="Alle", command=lambda: self.controller.combat_handler.reset_initiative("All"))
        reset_menu.add_command(label="Nur Gegner", command=lambda: self.controller.combat_handler.reset_initiative("Gegner"))
        reset_menu.add_command(label="Nur Spieler", command=lambda: self.controller.combat_handler.reset_initiative("Spieler"))
        reset_menu.add_command(label="Nur NPCs", command=lambda: self.controller.combat_handler.reset_initiative("NPC"))
        reset_btn.config(menu=reset_menu)
        reset_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="↩ Undo", command=self.controller.history_manager.undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="↪ Redo", command=self.controller.history_manager.redo).pack(side=tk.LEFT, padx=5)

        self.round_label = ttk.Label(control_frame, text=f"Runde: 1", font=FONTS["large"], background=self.colors["bg"])
        self.round_label.pack(side=tk.RIGHT, padx=20)

        bottom_content = ttk.Frame(self)
        bottom_content.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(bottom_content, text="Kampfprotokoll", style="Card.TLabelframe")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.log = tk.Text(log_frame, height=8, state="normal", bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"], font=FONTS["log"])
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scrollbar.set)

        self.dice_roller = DiceRoller(bottom_content, self.colors)
        self.dice_roller.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.log:
            self.log.configure(bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"])
        if self.round_label:
            self.round_label.configure(background=self.colors["bg"], foreground=self.colors["fg"])
        if self.dice_roller:
            self.dice_roller.update_colors(colors)

