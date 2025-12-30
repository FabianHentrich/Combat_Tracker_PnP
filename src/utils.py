import tkinter as tk
from tkinter import ttk
import random

def get_wuerfel_from_gewandtheit(gewandtheit: int) -> int:
    mapping = {
        1: 4,
        2: 6,
        3: 8,
        4: 10,
        5: 12,
        6: 20
    }
    # Einfache Validierung, um Abstürze zu vermeiden
    if gewandtheit < 1: return 4
    if gewandtheit > 6: return 20
    return mapping.get(gewandtheit, 20)

def wuerfle_initiative(gewandtheit: int) -> int:
    """Würfelt Initiative basierend auf Gewandtheit. Rückgabe des Wurfwerts."""
    wuerfel = get_wuerfel_from_gewandtheit(gewandtheit)
    return random.randint(1, wuerfel)

class ToolTip:
    """Klasse für Tooltips beim Hovern über Widgets."""
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tipwindow = None

    def showtip(self, event=None):
        text = self.text_func()
        if self.tipwindow or not text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        # wm_overrideredirect erwartet boolean (True/False) oder 1/0
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                       background="#ffffe0", foreground="#000000",
                       relief=tk.SOLID, borderwidth=1,
                       font=("Segoe UI", 9))
        label.pack(ipadx=5, ipady=2)

    def hidetip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def simple_input_dialog(root, title, prompt, default_value=""):
    """Helper function for input dialogs"""
    value = None

    def on_ok():
        nonlocal value
        value = entry.get()
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry("300x120")

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

