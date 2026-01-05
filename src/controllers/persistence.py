import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any

from src.utils.logger import setup_logging
from src.config import FILES, SAVES_DIR
from src.utils.save_manager import SaveManager
from src.utils.localization import translate

logger = setup_logging()

class PersistenceHandler:
    """
    Controller for saving and loading sessions.
    Manages file dialogs and delegates I/O to SaveManager.
    """
    def __init__(self, root: tk.Tk):
        self.root = root

    def save_session(self, state: Dict[str, Any]) -> Optional[str]:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=SAVES_DIR,
            filetypes=[(translate("dialog.file.json"), "*.json"), (translate("dialog.file.all"), "*.*")],
            title=translate("dialog.file.save_combat_title")
        )
        if not file_path:
            return None

        try:
            SaveManager.save_to_file(file_path, state)
            return file_path
        except Exception as e:
            logger.error(f"Error during save: {e}")
            messagebox.showerror(translate("dialog.error.title"), str(e))
            return None

    def load_session(self) -> Optional[Dict[str, Any]]:
        file_path = filedialog.askopenfilename(
            initialdir=SAVES_DIR,
            filetypes=[(translate("dialog.file.json"), "*.json"), (translate("dialog.file.all"), "*.*")],
            title=translate("dialog.file.load_combat_title")
        )
        if not file_path:
            return None

        try:
            return SaveManager.load_from_file(file_path)
        except Exception as e:
            logger.error(f"Error during load: {e}")
            messagebox.showerror(translate("dialog.error.title"), str(e))
            return None

    def autosave(self, state: Dict[str, Any]) -> None:
        """Automatically saves the current state to a file."""
        try:
            logger.info(f"Autosave running. Characters: {len(state.get('characters', []))}")
            SaveManager.save_to_file(FILES["autosave"], state)
        except Exception as e:
            logger.error(f"Autosave failed: {e}")

    def load_autosave(self) -> Optional[Dict[str, Any]]:
        """Loads the last automatically saved state."""
        try:
            return SaveManager.load_from_file(FILES["autosave"])
        except Exception as e:
            logger.warning(f"Could not load autosave: {e}")
            return None
