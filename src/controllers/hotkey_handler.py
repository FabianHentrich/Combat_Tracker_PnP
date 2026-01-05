import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, Callable, Optional

from src.config import HOTKEYS, FILES
from src.utils.logger import setup_logging
from src.ui.components.dialogs.hotkey_settings_dialog import HotkeySettingsDialog
from src.utils.localization import translate

logger = setup_logging()

class HotkeyHandler:
    """
    Manages keyboard shortcuts (hotkeys) for the application.
    """
    def __init__(self, root: tk.Tk, colors: Dict[str, str]):
        self.root = root
        self.colors = colors
        self.settings_dialog: Optional[HotkeySettingsDialog] = None
        self.callbacks: Dict[str, Callable[[], None]] = {}

    def setup_hotkeys(self, callbacks: Dict[str, Callable[[], None]]) -> None:
        """Binds keyboard shortcuts to the main window."""
        self.callbacks = callbacks
        self._bind_keys()

    def _bind_keys(self):
        """Internal method to bind keys based on the HOTKEYS config."""
        try:
            # Unbind all first to prevent duplicates on reload
            self.root.unbind_all('<KeyPress>')
            
            actions = list(self.callbacks.keys())

            for action in actions:
                hotkey = HOTKEYS.get(action)
                if hotkey:
                    # Use a closure to capture the correct callback for the lambda
                    def create_handler(cb):
                        return lambda e: self.safe_execute(e, cb)
                    
                    self.root.bind(hotkey, create_handler(self.callbacks[action]))

        except Exception as e:
            logger.error(f"Error binding hotkeys: {e}")

    def safe_execute(self, event: tk.Event, callback: Callable[[], None]) -> None:
        """
        Executes the callback only if an input field does not have focus.
        This prevents single-key hotkeys from firing while typing.
        """
        focused = self.root.focus_get()
        
        # Check if the event is from a single character key (e.g., 'a', 'b', 'space')
        # F-keys, Control, Alt, etc., have longer keysyms.
        # This is a more robust way to check for typing-related keys.
        is_char_key = len(event.keysym) == 1 or event.keysym == "space"

        if is_char_key and isinstance(focused, (tk.Entry, ttk.Entry, tk.Text)):
            return  # Don't execute callback if typing in an input field

        callback()

    def open_hotkey_settings(self) -> None:
        """Opens a window to edit hotkeys."""
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
        """Saves the new hotkeys to the JSON file and re-binds them."""
        try:
            HOTKEYS.update(new_hotkeys)
            with open(FILES["hotkeys"], 'w', encoding='utf-8') as f:
                json.dump(HOTKEYS, f, indent=4)
            
            self._bind_keys() # Re-bind all keys with the new configuration
            
            if self.settings_dialog and self.settings_dialog.winfo_exists():
                self.settings_dialog.destroy()

            messagebox.showinfo(translate("dialog.info.title"), translate("messages.hotkeys_saved"))

        except Exception as e:
            logger.error(f"Error saving hotkeys: {e}")
            messagebox.showerror(translate("dialog.error.title"), f"{translate('messages.save_failed')}: {e}")

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
