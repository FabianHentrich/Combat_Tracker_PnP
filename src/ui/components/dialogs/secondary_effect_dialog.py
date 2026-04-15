import tkinter as tk
from tkinter import ttk
from typing import Dict, List, TYPE_CHECKING
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.models.character import Character


class SecondaryEffectDialog:
    """
    Dialog to ask the DM which characters are affected by a secondary status effect,
    and to configure the rank and duration of the effect individually.
    """

    def __init__(
        self,
        parent: tk.Tk,
        effect_name: str,
        chars: List['Character'],
        colors: Dict[str, str],
        max_rank: int = 6,
    ):
        self.result: List['Character'] = []
        self.rank: int = 1
        self.duration: int = 3

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
            wraplength=320,
        ).pack(anchor="w", pady=(0, 10))

        # --- Rang & Dauer ---
        settings_frame = ttk.Frame(frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text=translate("action_panel.rank") + ":").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2
        )
        self._rank_var = tk.IntVar(value=1)
        ttk.Spinbox(
            settings_frame,
            from_=1, to=max_rank,
            textvariable=self._rank_var,
            width=5,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(settings_frame, text=translate("action_panel.duration") + ":").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=2
        )
        self._duration_var = tk.IntVar(value=3)
        ttk.Spinbox(
            settings_frame,
            from_=1, to=20,
            textvariable=self._duration_var,
            width=5,
        ).grid(row=1, column=1, sticky="w")

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 8))

        # --- Checkboxen pro Charakter ---
        self._vars: Dict['Character', tk.BooleanVar] = {}
        for char in chars:
            var = tk.BooleanVar(value=False)
            self._vars[char] = var
            label = f"{char.name}  (LP: {char.lp}/{char.max_lp})"
            ttk.Checkbutton(frame, text=label, variable=var).pack(anchor="w", pady=2)

        # --- Buttons ---
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

        # Zentrieren über Parent
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

        parent.wait_window(self.window)

    def _on_apply(self) -> None:
        self.result = [char for char, var in self._vars.items() if var.get()]
        try:
            self.rank = max(1, int(self._rank_var.get()))
            self.duration = max(1, int(self._duration_var.get()))
        except (ValueError, tk.TclError):
            self.rank = 1
            self.duration = 3
        self.window.destroy()