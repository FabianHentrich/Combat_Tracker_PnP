import tkinter as tk
from typing import TYPE_CHECKING
from src.utils.localization import translate
from src.config import AVAILABLE_LANGUAGES

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class MainMenu:
    """
    Encapsulates the creation and management of the main application menu.
    """
    def __init__(self, root: tk.Tk, controller: 'CombatTracker'):
        self.root = root
        self.controller = controller
        # Get handlers directly from the controller
        self.library_handler = self.controller.library_handler
        self.import_handler = self.controller.import_handler
        self._create_menu()

    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("menu.file"), menu=file_menu)
        file_menu.add_command(label=translate("menu.save_combat"), command=self.controller.save_session)
        file_menu.add_command(label=translate("menu.load_combat"), command=self.controller.load_session)
        file_menu.add_separator()
        file_menu.add_command(label=translate("menu.open_library"), command=self.library_handler.open_library_window)
        file_menu.add_command(label=translate("menu.import_excel"), command=self.import_handler.load_from_excel)
        file_menu.add_separator()
        file_menu.add_command(label=translate("menu.settings"), command=self.controller.open_hotkey_settings)
        file_menu.add_command(label=translate("menu.music_settings"), command=self.controller.open_audio_settings)
        file_menu.add_separator()
        file_menu.add_command(label=translate("menu.exit"), command=self.root.quit)

        # View Menu (for Theme and Language)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu) # This will be translated if you add a "view_menu" key

        # Theme Sub-Menu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=translate("menu.theme"), menu=theme_menu)
        from src.config import THEMES
        for theme_name in THEMES.keys():
            theme_menu.add_command(label=theme_name, command=lambda t=theme_name: self.controller.change_theme(t))

        # Language Sub-Menu
        lang_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=translate("menu.language"), menu=lang_menu)
        for lang_code in AVAILABLE_LANGUAGES:
            lang_name = "English" if lang_code == "en" else "Deutsch"
            lang_menu.add_command(label=lang_name, command=lambda lc=lang_code: self.controller.change_language(lc))
