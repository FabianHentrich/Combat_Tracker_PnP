import tkinter as tk
from tkinter import ttk
import random
from typing import Tuple, List, Callable, Optional
from src.config import FONTS, WINDOW_SIZE
from src.utils.localization import translate

class ToolTip:
    """Klasse für Tooltips beim Hovern über Widgets."""
    def __init__(self, widget: tk.Widget, text_func: Callable[[], str], color_provider: Optional[Callable[[], Tuple[str, str]]] = None):
        self.widget = widget
        self.text_func = text_func
        self.color_provider = color_provider
        self.tipwindow: Optional[tk.Toplevel] = None

    def showtip(self, event: Optional[tk.Event] = None) -> None:
        text = self.text_func()
        if self.tipwindow or not text:
            return

        bg = "#ffffe0"
        fg = "#000000"
        if self.color_provider:
            bg, fg = self.color_provider()

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        # wm_overrideredirect erwartet boolean (True/False) oder 1/0
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                       background=bg, foreground=fg,
                       relief=tk.SOLID, borderwidth=1,
                       font=FONTS["small"])
        label.pack(ipadx=5, ipady=2)

    def hidetip(self, event: Optional[tk.Event] = None) -> None:
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def simple_input_dialog(root: tk.Tk, title: str, prompt: str, default_value: str = "") -> Optional[str]:
    """Helper function for input dialogs"""
    value = None

    def on_ok() -> None:
        nonlocal value
        value = entry.get()
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry(WINDOW_SIZE["small_dialog"])

    ttk.Label(dialog, text=prompt).pack(pady=10)
    entry = ttk.Entry(dialog)
    entry.insert(0, default_value)
    entry.pack(pady=5)
    entry.focus()
    entry.bind('<Return>', lambda e: on_ok())
    ttk.Button(dialog, text=translate("common.ok"), command=on_ok).pack(pady=5)

    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
    return value

def generate_health_bar(current: int, maximum: int, length: int = 10) -> str:
    """Erstellt einen Text-Fortschrittsbalken mit Werten."""
    if maximum <= 0:
        return f"💀 {current}/{maximum}"

    percent = max(0, min(1, current / maximum))
    filled = int(length * percent)
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {current}/{maximum}"

def format_time(seconds: float) -> str:
    """Formatiert Sekunden in MM:SS Format."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
