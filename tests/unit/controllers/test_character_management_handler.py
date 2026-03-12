import pytest
from unittest.mock import MagicMock, patch

from src.controllers.character_management_handler import CharacterManagementHandler
from src.models.character import Character
from src.models.enums import CharacterType, ScopeType
from src.utils.localization import translate

@pytest.fixture
def mock_dependencies():
    """Provides a fixture for all dependencies of CharacterManagementHandler."""
    engine = MagicMock()
    history_manager = MagicMock()
    library_handler = MagicMock()
    root = MagicMock()
    view = MagicMock()
    colors = {"bg": "#000000", "fg": "#FFFFFF"}
    return engine, history_manager, library_handler, root, view, colors

@pytest.fixture
def handler(mock_dependencies):
    """Provides a CharacterManagementHandler instance with mocked dependencies."""
    return CharacterManagementHandler(*mock_dependencies)

# --- Tests ---

def test_add_character_quick_valid_input(handler):
    """Tests adding a character with valid quick-add data."""
    handler.view.get_quick_add_data.return_value = {
        "name": "Goblin", "lp": "15", "rp": "5", "sp": "0", "init": "10", "gew": "8", "level": "1",
        "type": CharacterType.ENEMY.value, "surprise": True
    }
    handler.add_character_quick()
    
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.insert_character.assert_called_once()
    
    # Check that the character passed to the engine has the correct attributes
    args, kwargs = handler.engine.insert_character.call_args
    new_char = args[0]
    assert isinstance(new_char, Character)
    assert new_char.name == "Goblin"
    assert new_char.lp == 15
    assert kwargs['surprise'] is True
    
    handler.view.clear_quick_add_fields.assert_called_once()

def test_add_character_quick_invalid_input(handler):
    """Tests graceful handling of invalid (non-numeric) input."""
    handler.view.get_quick_add_data.return_value = {"name": "Test", "lp": "abc"}
    handler.add_character_quick()
    handler.view.show_error.assert_called_once_with(translate("dialog.error.title"), translate("messages.use_valid_numbers"))

def test_add_character_no_name(handler):
    """Tests that an error is shown if the character name is missing."""
    handler.view.get_quick_add_data.return_value = {"name": "", "lp": "10"}
    handler.add_character_quick()
    handler.view.show_warning.assert_called_once_with(translate("dialog.error.title"), translate("messages.name_not_empty"))

def test_delete_character_no_selection(handler):
    """Tests that an error is shown if no character is selected."""
    handler.view.get_selected_char_id.return_value = None
    handler.delete_character()
    handler.view.show_error.assert_called_once_with(translate("dialog.error.title"), translate("messages.select_character_first"))

def test_delete_character_successful(handler):
    """Tests successful deletion of a selected character."""
    char_id = "char123"
    char_to_delete = Character("Dummy", 10, 5, 0, 12)
    char_to_delete.id = char_id
    
    handler.view.get_selected_char_id.return_value = char_id
    handler.engine.get_character_by_id.return_value = char_to_delete
    # Simulate the character being in the engine's list
    handler.engine.characters = [char_to_delete]
    
    handler.delete_character()
    
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.remove_character.assert_called_once_with(0) # Index 0

def test_delete_group(handler):
    """Tests deleting a group of characters (e.g., all enemies)."""
    handler.view.ask_yes_no.return_value = True
    handler.delete_group(CharacterType.ENEMY.value)
    
    handler.view.ask_yes_no.assert_called_once()
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.remove_characters_by_type.assert_called_once_with(CharacterType.ENEMY.value)

def test_edit_selected_char_no_selection(handler):
    """Tests that edit is aborted if no character is selected."""
    handler.view.get_selected_char_id.return_value = None
    handler.edit_selected_char()
    handler.view.show_error.assert_called_once_with(translate("dialog.error.title"), translate("messages.no_character_selected"))

@patch('src.controllers.character_management_handler.EditCharacterDialog')
def test_edit_selected_char_opens_dialog(MockEditDialog, handler):
    """Tests that the edit dialog is opened for a selected character."""
    char_id = "char123"
    char_to_edit = Character("Hero", 100, 20, 10, 15)
    char_to_edit.id = char_id
    
    handler.view.get_selected_char_id.return_value = char_id
    handler.engine.get_character_by_id.return_value = char_to_edit
    
    handler.edit_selected_char()
    
    MockEditDialog.assert_called_once()
    # Check that the dialog was instantiated with the correct character
    args, _ = MockEditDialog.call_args
    assert args[1] == char_to_edit

def test_manage_delete_selected(handler):
    """Tests that manage_delete calls delete_character for 'selected'."""
    handler.view.get_management_target.return_value = ScopeType.SELECTED
    with patch.object(handler, 'delete_character') as mock_delete:
        handler.manage_delete()
        mock_delete.assert_called_once()

def test_manage_delete_group(handler):
    """Tests that manage_delete calls delete_group for a group target."""
    handler.view.get_management_target.return_value = ScopeType.ALL_ENEMIES
    with patch.object(handler, 'delete_group') as mock_delete_group:
        handler.manage_delete()
        mock_delete_group.assert_called_once_with(CharacterType.ENEMY.value)

def test_manage_edit_selected(handler):
    """Tests that manage_edit calls edit_selected_char for 'selected'."""
    handler.view.get_management_target.return_value = ScopeType.SELECTED
    with patch.object(handler, 'edit_selected_char') as mock_edit:
        handler.manage_edit()
        mock_edit.assert_called_once()

def test_manage_edit_group(handler):
    """Tests that manage_edit shows info for bulk editing."""
    handler.view.get_management_target.return_value = ScopeType.ALL_ENEMIES
    handler.manage_edit()
    handler.view.show_info.assert_called_once_with(translate("dialog.info.title"), translate("messages.bulk_editing_not_available"))
