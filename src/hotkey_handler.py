import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, Any, Callable, TYPE_CHECKING
from .config import HOTKEYS
from .logger import setup_logging

if TYPE_CHECKING:
    from .main_window import CombatTracker

logger = setup_logging()

class HotkeyHandler:
    def __init__(self, tracker: 'CombatTracker', root: tk.Tk, colors: Dict[str, str]):
        self.tracker = tracker
        self.root = root
        self.colors = colors
        self.hotkey_buttons: Dict[str, ttk.Button] = {}

    def setup_hotkeys(self) -> None:
        """Bindet Tastaturkürzel an das Hauptfenster."""
        try:
            self.root.bind(HOTKEYS["next_turn"], lambda e: self.safe_execute(e, self.tracker.next_turn))
            self.root.bind(HOTKEYS["undo"], lambda e: self.safe_execute(e, self.tracker.undo_action))
            self.root.bind(HOTKEYS["redo"], lambda e: self.safe_execute(e, self.tracker.redo_action))
            self.root.bind(HOTKEYS["delete_char"], lambda e: self.safe_execute(e, self.tracker.delete_character))
            self.root.bind(HOTKEYS["focus_damage"], lambda e: self.safe_execute(e, self.tracker.action_value.focus_set))
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
        window = tk.Toplevel(self.root)
        window.title("Tastaturkürzel Einstellungen")
        window.geometry("400x300")
        window.configure(bg=self.colors["bg"])

        ttk.Label(window, text="Klicke auf einen Button und drücke eine Taste", font=('Segoe UI', 10, 'bold'), background=self.colors["bg"]).pack(pady=10)

        frame = ttk.Frame(window, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        labels = {
            "next_turn": "Nächster Zug",
            "undo": "Undo",
            "redo": "Redo",
            "delete_char": "Charakter löschen",
            "focus_damage": "Fokus auf Schaden"
        }

        self.hotkey_buttons = {}

        for key, label_text in labels.items():
            row_frame = ttk.Frame(frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=5)

            ttk.Label(row_frame, text=label_text, width=20, background=self.colors["panel"]).pack(side="left", padx=5)

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

    def save_hotkeys(self, window):
        """Speichert die Hotkeys in die JSON Datei und aktualisiert Bindings."""
        try:
            with open("hotkeys.json", 'w', encoding='utf-8') as f:
                json.dump(HOTKEYS, f, indent=4)

            self.setup_hotkeys()
            # Update menu accelerators if possible (requires recreating menu or accessing items)
            self.tracker.ui_layout.create_menu() # Re-create menu to update accelerators

            window.destroy()
            messagebox.showinfo("Info", "Hotkeys gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
