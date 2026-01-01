import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, Callable, TYPE_CHECKING
from src.utils.config import HOTKEYS, FONTS, WINDOW_SIZE, FILES
from src.utils.logger import setup_logging

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

logger = setup_logging()

class HotkeyHandler:
    def __init__(self, root: tk.Tk, colors: Dict[str, str]):
        self.root = root
        self.colors = colors
        self.hotkey_buttons: Dict[str, ttk.Button] = {}
        self.settings_window = None

    def setup_hotkeys(self, callbacks: Dict[str, Callable[[], None]]) -> None:
        """Bindet Tastaturkürzel an das Hauptfenster."""
        try:
            if "next_turn" in callbacks:
                self.root.bind(HOTKEYS["next_turn"], lambda e: self.safe_execute(e, callbacks["next_turn"]))
            if "undo" in callbacks:
                self.root.bind(HOTKEYS["undo"], lambda e: self.safe_execute(e, callbacks["undo"]))
            if "redo" in callbacks:
                self.root.bind(HOTKEYS["redo"], lambda e: self.safe_execute(e, callbacks["redo"]))
            if "delete_char" in callbacks:
                self.root.bind(HOTKEYS["delete_char"], lambda e: self.safe_execute(e, callbacks["delete_char"]))
            if "focus_damage" in callbacks:
                self.root.bind(HOTKEYS["focus_damage"], lambda e: self.safe_execute(e, callbacks["focus_damage"]))

            # Audio Hotkeys
            if "audio_play_pause" in callbacks:
                self.root.bind(HOTKEYS.get("audio_play_pause", "<Control-p>"), lambda e: self.safe_execute(e, callbacks["audio_play_pause"]))
            if "audio_next" in callbacks:
                self.root.bind(HOTKEYS.get("audio_next", "<Control-Right>"), lambda e: self.safe_execute(e, callbacks["audio_next"]))
            if "audio_prev" in callbacks:
                self.root.bind(HOTKEYS.get("audio_prev", "<Control-Left>"), lambda e: self.safe_execute(e, callbacks["audio_prev"]))
            if "audio_vol_up" in callbacks:
                self.root.bind(HOTKEYS.get("audio_vol_up", "<Control-Up>"), lambda e: self.safe_execute(e, callbacks["audio_vol_up"]))
            if "audio_vol_down" in callbacks:
                self.root.bind(HOTKEYS.get("audio_vol_down", "<Control-Down>"), lambda e: self.safe_execute(e, callbacks["audio_vol_down"]))
            if "audio_mute" in callbacks:
                self.root.bind(HOTKEYS.get("audio_mute", "<Control-m>"), lambda e: self.safe_execute(e, callbacks["audio_mute"]))

        except Exception as e:
            logger.error(f"Fehler beim Binden der Hotkeys: {e}")

    def safe_execute(self, event: tk.Event, callback: Callable[[], None]) -> None:
        """Führt den Callback nur aus, wenn kein Eingabefeld Fokus hat (für Einzeltasten-Hotkeys)."""
        focused = self.root.focus_get()

        # Wenn der Hotkey nur ein einzelnes Zeichen ist (z.B. Space, Buchstaben),
        # soll er nicht feuern, wenn man gerade tippt.
        # Wir prüfen, ob das fokussierte Widget ein Entry oder Text ist.
        if isinstance(focused, (tk.Entry, ttk.Entry, tk.Text)):
            # Liste der Tasten, die beim Tippen ignoriert werden sollen (wenn sie als Hotkey dienen)
            # Space ist der wichtigste Kandidat hier.
            if event.keysym.lower() == "space":
                return
            # Man könnte hier auch andere Tasten prüfen, falls nötig.

        callback()

    def open_hotkey_settings(self) -> None:
        """Öffnet ein Fenster zum Bearbeiten der Hotkeys."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title("Tastaturkürzel Einstellungen")
        window.geometry(WINDOW_SIZE["hotkeys"])
        window.configure(bg=self.colors["bg"])

        ttk.Label(window, text="Klicke auf einen Button und drücke eine Taste", font=FONTS["bold"]).pack(pady=10)

        frame = ttk.Frame(window, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        labels = {
            "next_turn": "Nächster Zug",
            "undo": "Undo",
            "redo": "Redo",
            "delete_char": "Charakter löschen",
            "focus_damage": "Fokus auf Schaden",
            "audio_play_pause": "Musik: Play/Pause",
            "audio_next": "Musik: Nächster Titel",
            "audio_prev": "Musik: Vorheriger Titel",
            "audio_vol_up": "Musik: Lauter",
            "audio_vol_down": "Musik: Leiser",
            "audio_mute": "Musik: Mute"
        }

        self.hotkey_buttons = {}

        for key, label_text in labels.items():
            row_frame = ttk.Frame(frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=5)

            ttk.Label(row_frame, text=label_text, width=20).pack(side="left", padx=5)

            current_key = HOTKEYS.get(key, "")
            btn = ttk.Button(row_frame, text=current_key)
            btn.pack(side="right", padx=5)
            btn.configure(command=lambda k=key, b=btn: self.change_hotkey(k, b))

            self.hotkey_buttons[key] = btn

        ttk.Button(window, text="Speichern & Schließen", command=lambda: self.save_hotkeys(window)).pack(pady=10)

    def change_hotkey(self, key_name: str, button: ttk.Button) -> None:
        """Wartet auf Tastendruck für neuen Hotkey."""
        button.configure(text="Drücke Taste...")

        def on_key(event: tk.Event) -> None:
            # Tastenkombination ermitteln
            keysym = event.keysym
            state = event.state

            # Modifiers
            parts = []
            if state & 0x0004: parts.append("Control")
            if state & 0x0001: parts.append("Shift")
            if state & 0x0008: parts.append("Alt")

            # Ignore modifier keys themselves
            if keysym in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]:
                return

            parts.append(keysym)
            new_hotkey = "<" + "-".join(parts) + ">"

            # Update UI
            button.configure(text=new_hotkey)
            HOTKEYS[key_name] = new_hotkey

            # Unbind listener (not strictly necessary as we bind to toplevel)

        # Capture next key press on the toplevel window
        button.winfo_toplevel().bind("<Key>", on_key)
        button.focus_set()

    def save_hotkeys(self, window: tk.Toplevel) -> None:
        """Speichert die neuen Hotkeys in die JSON-Datei."""
        try:
            with open(FILES["hotkeys"], 'w', encoding='utf-8') as f:
                json.dump(HOTKEYS, f, indent=4)

            self.setup_hotkeys() # Re-bind keys
            messagebox.showinfo("Erfolg", "Hotkeys gespeichert!")
            window.destroy()
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Hotkeys: {e}")
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")
