from typing import TYPE_CHECKING, Optional, Dict, Any
import re
import tkinter as tk

from src.models.character import Character
from src.models.enums import CharacterType, ScopeType
from src.ui.components.dialogs.edit_character_dialog import EditCharacterDialog
from src.config.defaults import MAX_GEW
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.ui.interfaces import ICombatView
    from src.controllers.library_handler import LibraryHandler

class CharacterManagementHandler:
    """
    Controller for adding, editing, and deleting characters.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', library_handler: 'LibraryHandler', root: tk.Tk, view: 'ICombatView', colors: Dict[str, str]):
        self.engine: 'CombatEngine' = engine
        self.history_manager: 'HistoryManager' = history_manager
        self.library_handler: 'LibraryHandler' = library_handler
        self.root: tk.Tk = root
        self.view = view
        self.colors = colors

        self.current_edit_dialog: Optional[EditCharacterDialog] = None
        self.current_edit_char_id: Optional[str] = None

    def add_character_quick(self) -> None:
        """Adds a character from the quick-add input fields."""
        data = self.view.get_quick_add_data()
        name = data["name"]

        if not name:
            self.view.show_warning(translate("dialog.error.title"), translate("messages.name_not_empty"))
            return

        try:
            self.history_manager.save_snapshot()
            lp = int(data["lp"]) if data["lp"] else 10
            rp = int(data["rp"]) if data["rp"] else 0
            sp = int(data["sp"]) if data["sp"] else 0
            init = int(data["init"]) if data["init"] else 0
            gew = int(data["gew"]) if data["gew"] else 1
            if gew > MAX_GEW:
                gew = MAX_GEW
                self.view.show_info(translate("dialog.info.title"), translate("messages.agility_set_to_max", max_gew=MAX_GEW))
            level = int(data["level"]) if data["level"] else 0
            char_type = data["type"]
            surprise = data["surprise"]

            new_char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type, level=level)
            self.engine.insert_character(new_char, surprise=surprise)

            self.view.clear_quick_add_fields()
            self.view.set_quick_add_defaults()

        except ValueError:
            self.view.show_error(translate("dialog.error.title"), translate("messages.use_valid_numbers"))
            self.history_manager.undo() # Roll back snapshot

    def delete_character(self) -> None:
        """Deletes the selected character."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error(translate("dialog.error.title"), translate("messages.select_character_first"))
            return

        deleted_char = self.engine.get_character_by_id(char_id)
        if deleted_char:
            self.history_manager.save_snapshot()
            # Find the actual index to remove
            actual_index = -1
            for i, char in enumerate(self.engine.characters):
                if char.id == char_id:
                    actual_index = i
                    break
            if actual_index != -1:
                self.engine.remove_character(actual_index)
        else:
            self.view.show_error(translate("dialog.error.title"), translate("messages.character_not_found"))

    def delete_group(self, char_type: str) -> None:
        """Deletes all characters of a specific type."""
        if self.view.ask_yes_no(translate("dialog.confirm.title"), translate("messages.really_delete_all", char_type=char_type)):
            self.history_manager.save_snapshot()
            self.engine.remove_characters_by_type(char_type)

    def edit_selected_char(self) -> None:
        """Edits all values of the selected character."""
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
        """Callback to save the changes."""
        self.history_manager.save_snapshot()
        self.engine.update_character(char, data)

    def on_character_double_click(self, event) -> None:
        """Opens the library for the selected character."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            return

        char = self.engine.get_character_by_id(char_id)
        if char:
            clean_name = re.sub(r'\s+\d+$', '', char.name)
            self.library_handler.open_library_window()
            self.library_handler.search_and_open(clean_name)

    def manage_edit(self) -> None:
        """Handles editing based on the selection in the management panel."""
        target = self.view.get_management_target()
        if target == ScopeType.SELECTED:
            self.edit_selected_char()
        else:
            self.view.show_info(translate("dialog.info.title"), translate("messages.bulk_editing_not_available"))

    def manage_delete(self) -> None:
        """Handles deletion based on the selection in the management panel."""
        target = self.view.get_management_target()
        if target == ScopeType.SELECTED:
            self.delete_character()
        elif target == ScopeType.ALL_ENEMIES:
            self.delete_group(CharacterType.ENEMY.value)
        elif target == ScopeType.ALL_PLAYERS:
            self.delete_group(CharacterType.PLAYER.value)
        elif target == ScopeType.ALL_NPCS:
            self.delete_group(CharacterType.NPC.value)
        elif target == ScopeType.ALL:
            if self.view.ask_yes_no(translate("dialog.confirm.title"), translate("messages.really_delete_all_characters")):
                self.history_manager.save_snapshot()
                self.engine.clear_all_characters()

    def _get_selected_char(self) -> Optional[Character]:
        """Helper method: Fetches the selected character via the view."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error(translate("dialog.error.title"), translate("messages.no_character_selected"))
            return None
        return self.engine.get_character_by_id(char_id)

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
