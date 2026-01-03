from typing import TYPE_CHECKING, Optional, Dict, Any
from src.models.character import Character
from src.models.enums import CharacterType
from src.ui.components.dialogs.edit_character_dialog import EditCharacterDialog
from src.config.defaults import MAX_GEW, DEFAULT_GEW
import re
import tkinter as tk

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.ui.interfaces import ICombatView
    from src.controllers.library_handler import LibraryHandler

class CharacterManagementHandler:
    """
    Controller für das Hinzufügen, Bearbeiten und Löschen von Charakteren.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager',
                 view_provider, library_handler: 'LibraryHandler', root: tk.Tk, colors: Dict[str, str]):
        self.engine = engine
        self.history_manager = history_manager
        self._view_provider = view_provider
        self.library_handler = library_handler
        self.root = root
        self.colors = colors

        self.current_edit_dialog: Optional[EditCharacterDialog] = None
        self.current_edit_char_id: Optional[str] = None

    @property
    def view(self) -> 'ICombatView':
        return self._view_provider()

    def add_character_quick(self) -> None:
        """Fügt einen Charakter aus den Eingabefeldern hinzu."""
        self.history_manager.save_snapshot()

        data = self.view.get_quick_add_data()
        name = data["name"]

        if not name:
            self.view.show_warning("Fehler", "Bitte einen Namen eingeben.")
            return

        try:
            lp = int(data["lp"]) if data["lp"] else 10
            rp = int(data["rp"]) if data["rp"] else 0
            sp = int(data["sp"]) if data["sp"] else 0
            init = int(data["init"]) if data["init"] else 0
            gew = int(data["gew"]) if data["gew"] else 1
            if gew > MAX_GEW:
                gew = MAX_GEW
                self.view.show_info("Info", f"Gewandtheit wurde auf das Maximum von {MAX_GEW} gesetzt.")
            level = int(data["level"]) if data["level"] else 0
            char_type = data["type"]
            surprise = data["surprise"]

            new_char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type, level=level)
            self.engine.insert_character(new_char, surprise=surprise)

            self.view.clear_quick_add_fields()
            self.view.set_quick_add_defaults()

        except ValueError:
            self.view.show_error("Fehler", "Bitte gültige Zahlenwerte eingeben.")

    def delete_character(self) -> None:
        """Löscht den ausgewählten Charakter."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        # Charakter finden
        deleted_char = None
        actual_index = -1

        for i, char in enumerate(self.engine.characters):
            if char.id == char_id:
                deleted_char = char
                actual_index = i
                break

        if deleted_char:
            self.history_manager.save_snapshot()
            self.engine.remove_character(actual_index)
        else:
            self.view.show_error("Fehler", "Charakter nicht gefunden (Interner Fehler).")

    def delete_group(self, char_type: str) -> None:
        """Löscht alle Charaktere eines bestimmten Typs."""
        if self.view.ask_yes_no("Bestätigung", f"Alle {char_type} wirklich löschen?"):
            self.history_manager.save_snapshot()
            self.engine.remove_characters_by_type(char_type)

    def edit_selected_char(self) -> None:
        """Bearbeitet alle Werte des ausgewählten Charakters."""
        char = self._get_selected_char()
        if not char:
            return

        if self.current_edit_dialog and self.current_edit_dialog.winfo_exists():
            if self.current_edit_char_id == char.id:
                self.current_edit_dialog.lift()
                self.current_edit_dialog.focus_force()
                return
            else:
                self.current_edit_dialog.destroy()

        self.current_edit_char_id = char.id
        self.current_edit_dialog = EditCharacterDialog(
            self.root,
            char,
            self.colors,
            lambda data: self._save_character(char, data)
        )

    def _save_character(self, char: 'Character', data: Dict[str, Any]) -> None:
        """Callback zum Speichern der Änderungen."""
        if self.history_manager:
            self.history_manager.save_snapshot()

        self.engine.update_character(char, data)

    def on_character_double_click(self, event) -> None:
        """Öffnet die Bibliothek für den ausgewählten Charakter."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            return

        char = self.engine.get_character_by_id(char_id)
        if char:
            # Remove numbers from name (e.g. "Goblin 1" -> "Goblin") for initial search
            clean_name = re.sub(r'\s+\d+$', '', char.name)

            self.library_handler.open_library_window()
            self.library_handler.search_and_open(clean_name)

    def manage_edit(self) -> None:
        """Handhabt das Bearbeiten basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.view.get_management_target()
        if target == "Ausgewählter Charakter":
            self.edit_selected_char()
        else:
            self.view.show_info("Info", "Massenbearbeitung ist derzeit nicht verfügbar.")

    def manage_delete(self) -> None:
        """Handhabt das Löschen basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.view.get_management_target()
        if target == "Ausgewählter Charakter":
            self.delete_character()
        elif target == "Alle Gegner":
            self.delete_group("Gegner")
        elif target == "Alle Spieler":
            self.delete_group("Spieler")
        elif target == "Alle NPCs":
            self.delete_group("NPC")
        elif target == "Alle Charaktere":
            if self.view.ask_yes_no("Bestätigung", "Wirklich ALLE Charaktere löschen?"):
                self.history_manager.save_snapshot()
                self.engine.clear_all_characters()

    def _get_selected_char(self) -> Optional[Character]:
        """Hilfsmethode: Holt den ausgewählten Charakter über die View."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error("Fehler", "Kein Charakter ausgewählt.")
            return None
        return self.engine.get_character_by_id(char_id)

