import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from src.config import WINDOW_SIZE, FONTS
from src.utils.localization import translate

class HotkeySettingsDialog:
    """
    Dialog-Fenster zum Bearbeiten der Tastaturkürzel.
    """
    def __init__(self, parent: tk.Tk, hotkeys: Dict[str, str], colors: Dict[str, str], on_save: Callable[[Dict[str, str]], None]):
        self.parent = parent
        self.hotkeys = hotkeys.copy() # Kopie bearbeiten
        self.colors = colors
        self.on_save = on_save
        self.hotkey_buttons: Dict[str, ttk.Button] = {}

        self.window = tk.Toplevel(parent)
        self.window.title(translate("dialog.hotkey_settings.title"))
        self.window.geometry(WINDOW_SIZE["hotkeys"])
        self.window.configure(bg=self.colors["bg"])

        self._setup_ui()

    def lift(self):
        self.window.lift()

    def focus_force(self):
        self.window.focus_force()

    def winfo_exists(self) -> bool:
        return self.window.winfo_exists()

    def _setup_ui(self):
        ttk.Label(self.window, text=translate("dialog.hotkey_settings.instruction"), font=FONTS["bold"]).pack(pady=10)

        frame = ttk.Frame(self.window, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        labels = {
            "next_turn": translate("hotkeys.next_turn"),
            "undo": translate("hotkeys.undo"),
            "redo": translate("hotkeys.redo"),
            "delete_char": translate("hotkeys.delete_char"),
            "focus_damage": translate("hotkeys.focus_damage"),
            "audio_play_pause": translate("hotkeys.audio_play_pause"),
            "audio_next": translate("hotkeys.audio_next"),
            "audio_prev": translate("hotkeys.audio_prev"),
            "audio_vol_up": translate("hotkeys.audio_vol_up"),
            "audio_vol_down": translate("hotkeys.audio_vol_down"),
            "audio_mute": translate("hotkeys.audio_mute")
        }

        for key, label_text in labels.items():
            self._create_hotkey_row(frame, key, label_text)

        ttk.Button(self.window, text=translate("common.save"), command=self._on_save).pack(pady=10)

    def _create_hotkey_row(self, parent, key, label_text):
        row_frame = ttk.Frame(parent, style="Card.TFrame")
        row_frame.pack(fill="x", pady=5)

        ttk.Label(row_frame, text=label_text, width=20).pack(side="left", padx=5)

        current_key = self.hotkeys.get(key, "")
        btn = ttk.Button(row_frame, text=current_key)
        btn.pack(side="right", padx=5)
        btn.configure(command=lambda k=key, b=btn: self._start_listening(k, b))

        self.hotkey_buttons[key] = btn

    def _start_listening(self, key_name: str, button: ttk.Button) -> None:
        """Wartet auf Tastendruck für neuen Hotkey."""
        button.configure(text=translate("dialog.hotkey_settings.press_key"))

        def on_key(event: tk.Event) -> None:
            new_hotkey = self._get_hotkey_string_from_event(event)
            if not new_hotkey:
                return

            # Update UI & Data
            button.configure(text=new_hotkey)
            self.hotkeys[key_name] = new_hotkey

            # Unbind listener
            self.window.unbind("<Key>")

        # Capture next key press on the toplevel window
        self.window.bind("<Key>", on_key)
        self.window.focus_set()

    def _get_hotkey_string_from_event(self, event: tk.Event) -> Optional[str]:
        keysym = event.keysym
        state = event.state

        # Ignore modifier keys themselves
        if keysym in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]:
            return None

        parts = []
        # Check modifiers (bitmasks might vary by OS, but standard tk usually works)
        if state & 0x0004: parts.append("Control")
        if state & 0x0001: parts.append("Shift")
        if state & 0x0008: parts.append("Alt")

        parts.append(keysym)
        return "<" + "-".join(parts) + ">"

    def _on_save(self):
        self.on_save(self.hotkeys)
        self.window.destroy()
