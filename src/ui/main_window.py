import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional
from src.models.character import Character
from src.controllers.import_handler import ImportHandler
from src.controllers.library_handler import LibraryHandler
from src.controllers.hotkey_handler import HotkeyHandler
from src.controllers.audio_controller import AudioController
from src.controllers.combat_action_handler import CombatActionHandler
from src.controllers.character_management_handler import CharacterManagementHandler
from src.ui.main_view import MainView
from src.ui.interfaces import ICombatView
from src.config import COLORS, WINDOW_SIZE, APP_TITLE, RULES
from src.core.engine import CombatEngine
from src.controllers.persistence import PersistenceHandler
from src.core.history import HistoryManager
from src.utils.logger import setup_logging
from src.models.enums import EventType

logger = setup_logging()

class CombatTracker:
    """
    Hauptklasse der Anwendung (Controller).
    Verbindet die UI (View) mit der Logik (CombatEngine).
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE["main"])

        # --- Modern Dark Theme Configuration ---
        self.colors: Dict[str, str] = COLORS

        self.engine = CombatEngine()

        self.history_manager = HistoryManager(self.engine)
        self.persistence_handler = PersistenceHandler(self.root)
        self.import_handler = ImportHandler(self.engine, self.history_manager, self.root, self.colors)
        self.library_handler = LibraryHandler(self.engine, self.history_manager, self.root, self.colors)
        self.hotkey_handler = HotkeyHandler(self.root, self.colors)
        self.combat_handler = CombatActionHandler(self.engine, self.history_manager, lambda: self.view)
        self.character_handler = CharacterManagementHandler(
            self.engine,
            self.history_manager,
            lambda: self.view,
            self.library_handler,
            self.root,
            self.colors
        )
        self.audio_controller = AudioController()
        if not self.audio_controller.is_initialized:
            error_msg = self.audio_controller.init_error or "Unbekannter Fehler"
            messagebox.showwarning(
                "Audio deaktiviert",
                f"Das Audio-System konnte nicht initialisiert werden.\nGrund: {error_msg}\n\nAudio-Funktionen sind deaktiviert."
            )

        self.audio_settings_window = None

        # View initialisieren
        self.view: ICombatView = MainView(self, self.root)
        self.view.setup_ui()

        # Subscribe to engine events
        self.engine.subscribe(EventType.UPDATE, self.view.update_listbox)
        self.engine.subscribe(EventType.LOG, self.log_message)

        self.root.configure(bg=self.colors["bg"])

        # Initial Theme Application
        self.view.update_colors(self.colors)

        # Hotkeys setup
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

        logger.info(f"Anwendung gestartet: {APP_TITLE}")

    def open_hotkey_settings(self) -> None:
        """Öffnet das Fenster für die Hotkey-Einstellungen."""
        self.hotkey_handler.open_hotkey_settings()

    def open_audio_settings(self) -> None:
        """Öffnet das Fenster für die Audio-Einstellungen."""
        if self.audio_settings_window and self.audio_settings_window.winfo_exists():
            self.audio_settings_window.lift()
            self.audio_settings_window.focus_force()
            return

        from src.ui.components.audio.audio_settings_view import AudioSettingsWindow
        self.audio_settings_window = AudioSettingsWindow(self.root, self.audio_controller, self.colors)


    def save_session(self) -> None:
        state = self.engine.get_state()
        state["audio"] = self.audio_controller.get_state()
        file_path = self.persistence_handler.save_session(state)
        if file_path:
            self.log_message(f"Kampf gespeichert unter: {file_path}")

    def load_session(self) -> None:
        state = self.persistence_handler.load_session()
        if state:
            if "audio" in state:
                self.audio_controller.load_state(state["audio"])
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.view.update_listbox()
            self.log_message("Kampf geladen.")

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
            self.log_message("Autosave geladen.")

    def log_message(self, msg: str) -> None:
        """Schreibt eine Nachricht in das Log-Fenster."""
        self.view.log_message(msg)


    def change_theme(self, theme_name: str) -> None:
        """Wechselt das Farbschema der Anwendung."""
        from src.config import THEMES
        if theme_name not in THEMES:
            return

        new_colors = THEMES[theme_name]
        self.colors = new_colors
        self.view.update_colors(new_colors)
        self.import_handler.colors = new_colors
        self.library_handler.update_colors(new_colors)
        self.hotkey_handler.colors = new_colors
        self.character_handler.colors = new_colors


        self.log_message(f"Theme gewechselt zu: {theme_name}")

    # --- Audio Hotkey Helpers ---
    # (Removed as logic moved to AudioController)

