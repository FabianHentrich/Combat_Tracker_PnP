import tkinter as tk
from tkinter import ttk
from typing import Dict
from src.config import FONTS

class StyleManager:
    """Verwaltet die ttk-Styles für die Anwendung."""

    def __init__(self, root: tk.Tk):
        self.root = root

    def configure_styles(self, colors: Dict[str, str]) -> None:
        """Konfiguriert die Styles basierend auf dem Farbschema."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.colors = colors

        self._configure_defaults()
        self._configure_buttons()
        self._configure_inputs()
        self._configure_treeview()
        self._configure_custom_cards()

    def _configure_defaults(self):
        self.style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], font=FONTS["main"])
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])

    def _configure_buttons(self):
        # Button
        self.style.configure("TButton",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        borderwidth=1,
                        focuscolor=self.colors["accent"],
                        lightcolor=self.colors["panel"],
                        darkcolor=self.colors["panel"],
                        bordercolor=self.colors["fg"])

        self.style.map("TButton",
                  background=[('pressed', self.colors["accent"]), ('active', self.colors["accent"]), ('!disabled', self.colors["panel"])],
                  foreground=[('disabled', '#888888'), ('!disabled', self.colors["fg"])],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

        # Checkbutton
        self.style.configure("TCheckbutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        indicatorbackground=self.colors["entry_bg"],
                        indicatorforeground=self.colors["fg"])

        self.style.map("TCheckbutton",
                  background=[('active', self.colors["bg"])],
                  indicatorbackground=[('active', self.colors["entry_bg"])])

    def _configure_inputs(self):
        # Common config for input widgets
        input_widgets = ["TEntry", "TCombobox", "TSpinbox"]

        for widget in input_widgets:
            self.style.configure(widget,
                            fieldbackground=self.colors["entry_bg"],
                            background=self.colors["entry_bg"],
                            foreground=self.colors["fg"],
                            lightcolor=self.colors["entry_bg"],
                            darkcolor=self.colors["entry_bg"],
                            bordercolor=self.colors["fg"])

            # Specific additions
            if widget == "TEntry":
                self.style.configure(widget, insertcolor=self.colors["fg"])
            else: # Combobox & Spinbox
                self.style.configure(widget, arrowcolor=self.colors["fg"])

        # Mappings
        self.style.map("TEntry",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!disabled', self.colors["entry_bg"])],
                  foreground=[('!disabled', self.colors["fg"])])

        self.style.map("TCombobox",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  selectbackground=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  selectforeground=[('readonly', self.colors["fg"]), ('!readonly', self.colors["fg"])],
                  background=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  foreground=[('readonly', self.colors["fg"]), ('!readonly', self.colors["fg"])])

        self.style.map("TSpinbox",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!disabled', self.colors["entry_bg"])],
                  foreground=[('!disabled', self.colors["fg"])],
                  background=[('!disabled', self.colors["entry_bg"])])

        # Combobox Listbox options (Tkinter options database)
        self.root.option_add('*TCombobox*Listbox.background', self.colors["entry_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors["fg"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors["bg"])

        # Scale
        self.style.configure("Horizontal.TScale",
                        background=self.colors["accent"],
                        troughcolor=self.colors["entry_bg"],
                        bordercolor=self.colors["fg"],
                        lightcolor=self.colors["accent"],
                        darkcolor=self.colors["accent"])

        self.style.map("Horizontal.TScale",
                  background=[('pressed', self.colors["fg"]), ('active', self.colors["accent"])])

    def _configure_treeview(self):
        self.style.configure("Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["panel"],
                        borderwidth=0)
        self.style.configure("Treeview.Heading",
                        background=self.colors["panel"],
                        foreground=self.colors["accent"],
                        borderwidth=1)
        self.style.map("Treeview", background=[('selected', self.colors["accent"])])

    def _configure_custom_cards(self):
        self.style.configure("Card.TFrame", background=self.colors["panel"])
        self.style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["fg"], bordercolor=self.colors["fg"])
        self.style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent"])
        self.style.configure("Card.TLabel", background=self.colors["panel"], foreground=self.colors["fg"])
        self.style.configure("Card.TCheckbutton", background=self.colors["panel"], foreground=self.colors["fg"],
                        indicatorbackground=self.colors["entry_bg"], indicatorforeground=self.colors["fg"])
        self.style.map("Card.TCheckbutton",
                  background=[('active', self.colors["panel"])],
                  indicatorbackground=[('active', self.colors["entry_bg"])])

