import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any
from src.utils.logger import setup_logging
from src.config import FILES, SAVES_DIR
from src.utils.save_manager import SaveManager

logger = setup_logging()

class PersistenceHandler:
    """
    Controller für das Speichern und Laden.
    Verwaltet Dateidialoge und delegiert IO an SaveManager.
    """
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

        try:
            SaveManager.save_to_file(file_path, state)
            return file_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
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
            return SaveManager.load_from_file(file_path)
        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}")
            messagebox.showerror("Fehler beim Laden", str(e))
            return None

    def autosave(self, state: Dict[str, Any]) -> None:
        """Speichert den aktuellen Zustand automatisch in eine Datei."""
        try:
            # Debug-Log, um sicherzustellen, dass autosave aufgerufen wird
            logger.info(f"Autosave wird ausgeführt. Charaktere: {len(state.get('characters', []))}")
            SaveManager.save_to_file(FILES["autosave"], state)
        except Exception as e:
            logger.error(f"Autosave fehlgeschlagen: {e}")

    def load_autosave(self) -> Optional[Dict[str, Any]]:
        """Lädt den zuletzt automatisch gespeicherten Zustand."""
        try:
            return SaveManager.load_from_file(FILES["autosave"])
        except Exception as e:
            # Nur loggen, kein Popup beim Start, wenn Autosave kaputt/nicht da ist (könnte nerven)
            # Oder doch Popup? Im Original war Popup. Ich lasse es mal, aber vielleicht als Warning.
            logger.warning(f"Konnte Autosave nicht laden: {e}")
            return None
