import tkinter as tk
from tkinter import ttk
import random
from typing import Tuple, List, Callable, Optional
from .config import FONTS, WINDOW_SIZE, GEW_TO_DICE

def roll_exploding_dice(sides: int) -> Tuple[int, List[int]]:
    """
    Simuliert einen explodierenden Würfelwurf.
    Wenn die höchste Augenzahl gewürfelt wird, darf erneut gewürfelt werden.
    Gibt die Summe und die Liste der Einzelwürfe zurück.
    """
    rolls = []
    while True:
        roll = random.randint(1, sides)
        rolls.append(roll)
        if roll != sides:
            break
        # Safety break to prevent infinite loops
        if len(rolls) > 20:
            break
    return sum(rolls), rolls

def get_wuerfel_from_gewandtheit(gewandtheit: int) -> int:
    # Einfache Validierung, um Abstürze zu vermeiden
    if gewandtheit < 1: return 4
    if gewandtheit > 6: return 20
    return GEW_TO_DICE.get(gewandtheit, 20)

def wuerfle_initiative(gewandtheit: int) -> int:
    """Würfelt Initiative basierend auf Gewandtheit (mit explodierenden Würfeln). Rückgabe des Wurfwerts."""
    wuerfel = get_wuerfel_from_gewandtheit(gewandtheit)
    total, _ = roll_exploding_dice(wuerfel)
    return total

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
    ttk.Button(dialog, text="OK", command=on_ok).pack(pady=5)

    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
    return value

def generate_health_bar(current: int, maximum: int, length: int = 10) -> str:
    """Erstellt einen Text-Fortschrittsbalken mit Werten."""
    if maximum <= 0:
        return f"💀 {current}/{maximum}"

    ratio = max(0, min(1, current / maximum))
    filled_len = int(round(length * ratio))

    # Balken bauen
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"{bar} {current}/{maximum}"
