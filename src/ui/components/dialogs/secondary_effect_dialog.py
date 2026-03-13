import tkinter as tk
from tkinter import ttk
from typing import Dict, List, TYPE_CHECKING
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.models.character import Character


class SecondaryEffectDialog:
    """
    Dialog to ask the DM which characters are affected by a secondary status effect.
    Shows a checkbox per target so each can be confirmed individually.
    """

    def __init__(self, parent: tk.Tk, effect_name: str, chars: List['Character'], colors: Dict[str, str]):
        self.result: List['Character'] = []

        self.window = tk.Toplevel(parent)
        self.window.title(translate("dialog.secondary_effect.title", effect=effect_name))
        self.window.configure(bg=colors["bg"])
        self.window.resizable(False, False)
        self.window.grab_set()  # modal

        frame = ttk.Frame(self.window, padding="16", style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text=translate("dialog.secondary_effect.prompt", effect=effect_name),
            style="TLabel",
            wraplength=300,
        ).pack(anchor="w", pady=(0, 12))

        # One checkbox per character
        self._vars: Dict['Character', tk.BooleanVar] = {}
        for char in chars:
            var = tk.BooleanVar(value=False)
            self._vars[char] = var
            label = f"{char.name}  (LP: {char.lp}/{char.max_lp})"
            ttk.Checkbutton(frame, text=label, variable=var).pack(anchor="w", pady=2)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(14, 0))

        ttk.Button(
            btn_frame,
            text=translate("dialog.secondary_effect.apply"),
            command=self._on_apply,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        ttk.Button(
            btn_frame,
            text=translate("common.cancel"),
            command=self.window.destroy,
        ).pack(side=tk.RIGHT)

        # Centre dialog over parent
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

        parent.wait_window(self.window)

    def _on_apply(self) -> None:
        self.result = [char for char, var in self._vars.items() if var.get()]
        self.window.destroy()