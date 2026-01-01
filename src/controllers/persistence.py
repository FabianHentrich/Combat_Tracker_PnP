import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any
from src.utils.logger import setup_logging
from src.utils.config import FILES, SAVES_DIR

logger = setup_logging()

DATA_VERSION = 1

class PersistenceHandler:
    def __init__(self, root: tk.Tk):
        self.root = root

    def save_session(self, state: Dict[str, Any]) -> Optional[str]:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=SAVES_DIR,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Kampf speichern"
        )
        if not file_path:
            return None

        data = {
            "version": DATA_VERSION,
            "state": state
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return file_path
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))
            return None

    def load_session(self) -> Optional[Dict[str, Any]]:
        file_path = filedialog.askopenfilename(
            initialdir=SAVES_DIR,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Kampf laden"
        )
        if not file_path:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Version check / migration
            if "version" in data and "state" in data:
                return data["state"]
            else:
                # Old format (direct state)
                return data

        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))
            return None

    def autosave(self, state: Dict[str, Any]) -> None:
        """Speichert den aktuellen Zustand automatisch in eine Datei."""
        data = {
            "version": DATA_VERSION,
            "state": state
        }
        try:
            with open(FILES["autosave"], 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Autosave fehlgeschlagen: {e}")

    def load_autosave(self) -> Optional[Dict[str, Any]]:
        """Lädt den zuletzt automatisch gespeicherten Zustand."""
        try:
            with open(FILES["autosave"], 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "version" in data and "state" in data:
                return data["state"]
            else:
                return data
        except Exception as e:
            messagebox.showerror("Fehler beim Laden des Autosaves", str(e))
            return None
