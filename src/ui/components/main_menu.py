import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class MainMenu:
    """
    Kapselt die Erstellung und Verwaltung des Hauptmenüs.
    """
    def __init__(self, root: tk.Tk, controller: 'CombatTracker'):
        self.root = root
        self.controller = controller
        self._create_menu()

    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)

        file_menu.add_command(label="Kampf speichern...", command=self.controller.save_session)
        file_menu.add_command(label="Kampf laden...", command=self.controller.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Bibliothek öffnen", command=self.controller.library_handler.open_library_window)
        file_menu.add_command(label="Gegner importieren (Excel)...", command=self.controller.import_handler.load_from_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Einstellungen...", command=self.controller.open_hotkey_settings)
        file_menu.add_command(label="Musikeinstellungen...", command=self.controller.open_audio_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)

        # Theme Menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        from src.config import THEMES
        for theme_name in THEMES.keys():
            theme_menu.add_command(label=theme_name, command=lambda t=theme_name: self.controller.change_theme(t))

