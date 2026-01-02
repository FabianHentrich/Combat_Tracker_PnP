import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, Callable, TYPE_CHECKING, Optional
from src.config import HOTKEYS, FILES
from src.utils.logger import setup_logging
from src.ui.components.dialogs.hotkey_settings_dialog import HotkeySettingsDialog

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

logger = setup_logging()

class HotkeyHandler:
    def __init__(self, root: tk.Tk, colors: Dict[str, str]):
        self.root = root
        self.colors = colors
        self.settings_dialog: Optional[HotkeySettingsDialog] = None
        self.callbacks: Dict[str, Callable[[], None]] = {}

    def setup_hotkeys(self, callbacks: Dict[str, Callable[[], None]]) -> None:
        """Bindet Tastaturkürzel an das Hauptfenster."""
        self.callbacks = callbacks
        self._bind_keys()

    def _bind_keys(self):
        """Interne Methode zum Binden der Keys basierend auf HOTKEYS config."""
        try:
            # Liste aller unterstützten Hotkey-Aktionen
            actions = [
                "next_turn", "undo", "redo", "delete_char", "focus_damage",
                "audio_play_pause", "audio_next", "audio_prev", "audio_vol_up", "audio_vol_down", "audio_mute"
            ]

            for action in actions:
                if action in self.callbacks:
                    hotkey = HOTKEYS.get(action)
                    if hotkey:
                        # Wir nutzen default argument cb=..., um den aktuellen Wert von action zu binden
                        self.root.bind(hotkey, lambda e, cb=self.callbacks[action]: self.safe_execute(e, cb))

        except Exception as e:
            logger.error(f"Fehler beim Binden der Hotkeys: {e}")

    def safe_execute(self, event: tk.Event, callback: Callable[[], None]) -> None:
        """Führt den Callback nur aus, wenn kein Eingabefeld Fokus hat (für Einzeltasten-Hotkeys)."""
        focused = self.root.focus_get()

        # Wenn der Hotkey nur ein einzelnes Zeichen ist (z.B. Space, Buchstaben),
        # soll er nicht feuern, wenn man gerade tippt.
        if isinstance(focused, (tk.Entry, ttk.Entry, tk.Text)):
            if event.keysym.lower() == "space":
                return
            # Hier könnte man weitere Checks hinzufügen, falls nötig.

        callback()

    def open_hotkey_settings(self) -> None:
        """Öffnet ein Fenster zum Bearbeiten der Hotkeys."""
        if self.settings_dialog and self.settings_dialog.winfo_exists():
            self.settings_dialog.lift()
            self.settings_dialog.focus_force()
            return

        self.settings_dialog = HotkeySettingsDialog(
            self.root,
            HOTKEYS,
            self.colors,
            self.save_hotkeys
        )

    def save_hotkeys(self, new_hotkeys: Dict[str, str]) -> None:
        """Speichert die neuen Hotkeys in die JSON-Datei."""
        try:
            HOTKEYS.update(new_hotkeys)

            with open(FILES["hotkeys"], 'w', encoding='utf-8') as f:
                json.dump(HOTKEYS, f, indent=4)

            self._bind_keys()
            messagebox.showinfo("Erfolg", "Hotkeys gespeichert!")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Hotkeys: {e}")
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


