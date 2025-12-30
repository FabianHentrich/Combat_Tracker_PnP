import json
import tkinter as tk
from tkinter import filedialog, messagebox

class PersistenceHandler:
    def __init__(self, tracker, root):
        self.tracker = tracker
        self.root = root

    def save_session(self):
        state = self.tracker.engine.get_state()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Kampf speichern"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            self.tracker.log_message(f"Kampf gespeichert unter: {file_path}")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def load_session(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Kampf laden"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.tracker.engine.load_state(state)
            self.tracker.initiative_rolled = (self.tracker.engine.turn_index != -1)
            self.tracker.update_listbox()
            self.tracker.log_message(f"Kampf geladen aus: {file_path}")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))

    def autosave(self):
        """Speichert den aktuellen Zustand automatisch in eine Datei."""
        try:
            state = self.tracker.engine.get_state()
            with open("autosave.json", 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Autosave fehlgeschlagen: {e}")
