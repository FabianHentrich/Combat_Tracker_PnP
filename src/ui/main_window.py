import tkinter as tk
from tkinter import messagebox
import os
from typing import Dict, Optional

# Core and Services
from src.core.engine import CombatEngine
from src.core.history import HistoryManager

# Controllers
from src.controllers.import_handler import ImportHandler
from src.controllers.library_handler import LibraryHandler
from src.controllers.hotkey_handler import HotkeyHandler
from src.controllers.audio_controller import AudioController
from src.controllers.combat_action_handler import CombatActionHandler
from src.controllers.character_management_handler import CharacterManagementHandler
from src.controllers.persistence import PersistenceHandler

# UI and Config
from src.ui.main_view import MainView
from src.ui.interfaces import ICombatView
from src.config import COLORS, WINDOW_SIZE, FILES, AVAILABLE_LANGUAGES
from src.ui.components.audio.audio_settings_view import AudioSettingsWindow

# Models and Utils
from src.models.enums import EventType
from src.utils.logger import setup_logging
from src.utils.localization import translate, localization_manager

logger = setup_logging()

class CombatTracker:
    """
    Main application class.
    Initializes and connects the UI to the application logic.
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(translate("app.title"))
        self.root.geometry(WINDOW_SIZE["main"])

        self.colors: Dict[str, str] = COLORS

        # --- Core Components ---
        self.engine = CombatEngine()
        self.history_manager = HistoryManager(self.engine)

        # --- UI Components (creation only) ---
        self.view: ICombatView = MainView(self, self.root)

        # --- Handlers (must be created before view.setup_ui()) ---
        self.audio_controller = AudioController()
        self.persistence_handler = PersistenceHandler(self.root)
        self.hotkey_handler = HotkeyHandler(self.root, self.colors)
        self.library_handler = LibraryHandler(self.root, self.engine, self.history_manager, self.colors)
        self.import_handler = ImportHandler(self.engine, self.history_manager, self.root, self.colors)
        self.character_handler = CharacterManagementHandler(self.engine, self.history_manager, self.library_handler, self.root, self.view, self.colors)
        self.combat_handler = CombatActionHandler(self.engine, self.history_manager, self.view)

        # --- UI Setup (now that all handlers exist) ---
        self.view.setup_ui()

        # --- Final Setup ---
        if not self.audio_controller.is_initialized:
            error_msg = self.audio_controller.init_error or translate("messages.unknown_error")
            messagebox.showwarning(
                translate("dialog.error.title"),
                f"{translate('messages.audio_disabled')}\n{translate('messages.reason')}: {error_msg}\n\n{translate('messages.audio_functions_disabled')}"
            )

        self.audio_settings_window = None

        self.engine.subscribe(EventType.UPDATE, self.view.update_listbox)
        self.engine.subscribe(EventType.UPDATE, self.autosave)
        self.engine.subscribe(EventType.LOG, self.log_message)

        self.root.configure(bg=self.colors["bg"])
        self.view.update_colors(self.colors)

        self._setup_hotkeys()
        self._handle_startup_and_shutdown()

        logger.info(f"Application started: {translate('app.title')}")

    def _setup_hotkeys(self) -> None:
        """Configures hotkey callbacks."""
        hotkey_callbacks = {
            "next_turn": self.combat_handler.next_turn,
            "undo": self.history_manager.undo,
            "redo": self.history_manager.redo,
            "delete_char": self.character_handler.delete_character,
            "focus_damage": self.view.focus_damage_input,
            "audio_play_pause": self.audio_controller.toggle_playback,
            "audio_next": self.audio_controller.next_track,
            "audio_prev": self.audio_controller.prev_track,
            "audio_vol_up": self.audio_controller.increase_volume,
            "audio_vol_down": self.audio_controller.decrease_volume,
            "audio_mute": self.audio_controller.toggle_mute
        }
        self.hotkey_handler.setup_hotkeys(hotkey_callbacks)

    def _handle_startup_and_shutdown(self) -> None:
        """Manages crash recovery and clean shutdown procedures."""
        lock_file = FILES["lock"]
        if os.path.exists(lock_file):
            logger.warning("Crash detected. Attempting to load autosave.")
            if messagebox.askyesno(translate("dialog.confirm.title"), translate("messages.crash_detected")):
                self.load_autosave()
        else:
            try:
                with open(lock_file, 'w') as f: f.write("locked")
            except Exception as e:
                logger.error(f"Could not create lock file: {e}")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Removes the lock file on clean shutdown."""
        lock_file = FILES["lock"]
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except Exception as e:
                logger.error(f"Could not remove lock file: {e}")
        self.root.destroy()

    def open_hotkey_settings(self) -> None:
        self.hotkey_handler.open_hotkey_settings()

    def open_audio_settings(self) -> None:
        if self.audio_settings_window and self.audio_settings_window.winfo_exists():
            self.audio_settings_window.lift()
            self.audio_settings_window.focus_force()
            return

        self.audio_settings_window = AudioSettingsWindow(self.root, self.audio_controller, self.colors)

    def save_session(self) -> None:
        state = self.engine.get_state()
        state["audio"] = self.audio_controller.get_state()
        file_path = self.persistence_handler.save_session(state)
        if file_path:
            self.log_message(translate("messages.combat_saved", file_path=file_path))

    def load_session(self) -> None:
        state = self.persistence_handler.load_session()
        if state:
            if "audio" in state:
                self.audio_controller.load_state(state["audio"])
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.view.update_listbox()
            self.log_message(translate("messages.combat_loaded"))

    def autosave(self) -> None:
        state = self.engine.get_state()
        state["audio"] = self.audio_controller.get_state()
        self.persistence_handler.autosave(state)

    def load_autosave(self) -> None:
        state = self.persistence_handler.load_autosave()
        if state:
            if "audio" in state:
                self.audio_controller.load_state(state["audio"])
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.view.update_listbox()
            self.log_message(translate("messages.autosave_loaded"))

    def log_message(self, msg: str) -> None:
        self.view.log_message(msg)

    def change_theme(self, theme_name: str) -> None:
        from src.config import THEMES
        if theme_name not in THEMES: return

        new_colors = THEMES[theme_name]
        self.colors = new_colors
        
        # Manually update colors on all relevant components
        self.hotkey_handler.update_colors(new_colors)
        self.view.update_colors(new_colors)
        self.import_handler.update_colors(new_colors)
        self.character_handler.update_colors(new_colors)
        self.library_handler.update_colors(new_colors)

        self.log_message(translate("messages.theme_changed", theme_name=theme_name))

    def change_language(self, lang_code: str):
        """Changes the application language and redraws the UI."""
        if lang_code not in AVAILABLE_LANGUAGES:
            logger.warning(f"Language '{lang_code}' not available.")
            return

        localization_manager.set_language(lang_code)
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.__init__(self.root)
        
        logger.info(f"Language changed to {lang_code}.")
        self.log_message(f"Language changed to {lang_code}.")
