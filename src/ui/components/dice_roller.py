import tkinter as tk
from tkinter import ttk
import random
import logging
from typing import Dict, Any, List
from src.config import COLORS, FONTS, DICE_TYPES
from src.core.mechanics import roll_exploding_dice
from src.utils.localization import translate

logger = logging.getLogger("CombatTracker")

class DiceRoller(ttk.LabelFrame):
    ANIMATION_DURATION = 600  # ms
    ANIMATION_STEPS = 15

    def __init__(self, parent: tk.Widget, colors: Dict[str, str] = None, **kwargs: Any):
        super().__init__(parent, text=translate("dice_roller.title"), style="Card.TLabelframe", padding="10", **kwargs)
        self.colors: Dict[str, str] = colors if colors else COLORS

        self.result_var: tk.StringVar = tk.StringVar(value=translate("dice_roller.ready"))
        self.history_var: tk.StringVar = tk.StringVar(value="")
        self.is_rolling: bool = False

        self._create_ui()

    def _create_ui(self) -> None:
        # Top: Result Display
        display_frame = ttk.Frame(self)
        display_frame.pack(fill="x", pady=(0, 10))

        self.result_label = ttk.Label(display_frame, textvariable=self.result_var,
                                      font=FONTS["huge"], anchor="center",
                                      foreground=self.colors["accent"])
        self.result_label.pack(fill="x")

        self.history_label = ttk.Label(display_frame, textvariable=self.history_var,
                                       font=FONTS["small"], anchor="center",
                                       foreground=self.colors["fg"])
        self.history_label.pack(fill="x")

        # Middle: Dice Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="both", expand=True)

        dice_types = DICE_TYPES

        # Grid layout for buttons (3 Spalten)
        for i, sides in enumerate(dice_types):
            btn = ttk.Button(btn_frame, text=f"d{sides}",
                             command=lambda s=sides: self.roll_dice(s))
            btn.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="ew")

        # Configure grid weights
        for i in range(3):
            btn_frame.columnconfigure(i, weight=1)

    def roll_dice(self, sides: int) -> None:
        if self.is_rolling:
            return

        self.is_rolling = True
        self.history_var.set(translate("dice_roller.rolling", sides=sides))

        # Animation parameters
        interval = self.ANIMATION_DURATION // self.ANIMATION_STEPS

        self._animate_roll(sides, self.ANIMATION_STEPS, interval)

    def _animate_roll(self, sides: int, steps_left: int, interval: int) -> None:
        if steps_left > 0:
            # Show random number
            fake_roll = random.randint(1, sides)
            self.result_var.set(str(fake_roll))
            self.after(interval, lambda: self._animate_roll(sides, steps_left - 1, interval))
        else:
            # Final roll calculation
            self._finalize_roll(sides)

    @staticmethod
    def _get_roll_message(sides: int, total: int, rolls: List[int]) -> str:
        """Generates the log message for a dice roll. Pure logic, no UI."""
        roll_str = " + ".join(map(str, rolls))
        if len(rolls) > 1:
            return translate("dice_roller.result_exploded", sides=sides, roll_str=roll_str, total=total)
        else:
            return translate("dice_roller.result_normal", sides=sides, roll_str=roll_str)

    def _finalize_roll(self, sides: int) -> None:
        total, rolls = roll_exploding_dice(sides)
        self.result_var.set(str(total))

        msg = DiceRoller._get_roll_message(sides, total, rolls)

        self.history_var.set(msg)
        logger.info(f"DiceRoller: {msg}")

        self.is_rolling = False

    def update_colors(self, new_colors: Dict[str, str]) -> None:
        """Aktualisiert die Farben der UI-Elemente."""
        self.colors = new_colors
        if self.result_label and self.result_label.winfo_exists():
            self.result_label.configure(foreground=self.colors["accent"])
        if self.history_label and self.history_label.winfo_exists():
            self.history_label.configure(foreground=self.colors["fg"])
