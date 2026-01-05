import pytest
from unittest.mock import MagicMock, patch, ANY
from src.models.character import Character
from src.models.enums import StatType, CharacterType
from src.models.status_effects import PoisonEffect

# Mock tkinter before importing the dialog
@patch('tkinter.Toplevel')
def get_edit_dialog(MockToplevel):
    from src.ui.components.dialogs.edit_character_dialog import EditCharacterDialog
    
    mock_parent = MagicMock()
    mock_char = Character("Test", 100, 10, 5, 15)
    mock_colors = {"bg": "black"}
    mock_on_save = MagicMock()
    
    with patch.object(EditCharacterDialog, '_setup_ui'):
        dialog = EditCharacterDialog(mock_parent, mock_char, mock_colors, mock_on_save)
        
        # Manually mock the UI elements that _on_save_click depends on
        dialog.entries = {
            StatType.NAME.value: MagicMock(),
            StatType.TYPE.value: MagicMock(),
            StatType.LEVEL.value: MagicMock(),
            StatType.LP.value: MagicMock(),
            StatType.MAX_LP.value: MagicMock(),
            StatType.RP.value: MagicMock(),
            StatType.MAX_RP.value: MagicMock(),
            StatType.SP.value: MagicMock(),
            StatType.MAX_SP.value: MagicMock(),
            StatType.GEW.value: MagicMock(),
            StatType.INIT.value: MagicMock()
        }
        dialog.status_ui_entries = []
        dialog.translated_types = {"Player": CharacterType.PLAYER.value}
        dialog.window = MockToplevel() # The mocked Toplevel instance
        
    return dialog

@pytest.fixture
def dialog():
    """Provides an EditCharacterDialog instance with mocked UI elements."""
    return get_edit_dialog()

# --- _on_save_click Tests ---

def test_on_save_click_success(dialog):
    """Tests the successful collection and saving of character data."""
    # Configure mock UI element return values
    dialog.entries[StatType.NAME.value].get.return_value = "New Name"
    dialog.entries[StatType.TYPE.value].get.return_value = "Player"
    dialog.entries[StatType.LEVEL.value].get.return_value = "5"
    dialog.entries[StatType.LP.value].get.return_value = "80"
    dialog.entries[StatType.MAX_LP.value].get.return_value = "110"
    dialog.entries[StatType.RP.value].get.return_value = "12"
    dialog.entries[StatType.MAX_RP.value].get.return_value = "15"
    dialog.entries[StatType.SP.value].get.return_value = "3"
    dialog.entries[StatType.MAX_SP.value].get.return_value = "8"
    dialog.entries[StatType.GEW.value].get.return_value = "4"
    dialog.entries[StatType.INIT.value].get.return_value = "16"
    
    # Simulate one status effect in the UI
    status_row = {
        "effect": MagicMock(cget=MagicMock(return_value="POISON")),
        "rounds": MagicMock(get=MagicMock(return_value="3")),
        "rank": MagicMock(get=MagicMock(return_value="2"))
    }
    dialog.status_ui_entries.append(status_row)
    
    dialog._on_save_click()
    
    # 1. Check that the on_save callback was called
    dialog.on_save.assert_called_once()
    
    # 2. Check the data payload passed to the callback
    saved_data = dialog.on_save.call_args[0][0]
    assert saved_data[StatType.NAME.value] == "New Name"
    assert saved_data[StatType.LP.value] == 80
    assert saved_data[StatType.MAX_RP.value] == 15
    assert saved_data[StatType.CHAR_TYPE.value] == CharacterType.PLAYER.value
    
    # 3. Check the reconstructed status effect
    assert len(saved_data[StatType.STATUS.value]) == 1
    saved_effect = saved_data[StatType.STATUS.value][0]
    assert isinstance(saved_effect, PoisonEffect)
    assert saved_effect.duration == 3
    assert saved_effect.rank == 2
    
    # 4. Check that the window was destroyed
    dialog.window.destroy.assert_called_once()

@patch('src.ui.components.dialogs.edit_character_dialog.messagebox.showerror')
def test_on_save_click_invalid_number(mock_showerror, dialog):
    """Tests that a ValueError shows an error message and prevents saving."""
    dialog.entries[StatType.NAME.value].get.return_value = "Test"
    dialog.entries[StatType.LP.value].get.return_value = "abc" # Invalid number
    # Set other required fields to valid values
    for key, entry in dialog.entries.items():
        if key != StatType.LP.value and key != StatType.NAME.value:
            entry.get.return_value = "1"
    dialog.entries[StatType.TYPE.value].get.return_value = "Player"

    dialog._on_save_click()
    
    mock_showerror.assert_called_once()
    assert "Invalid input" in mock_showerror.call_args[0][1]
    dialog.on_save.assert_not_called()
    dialog.window.destroy.assert_not_called()

@patch('src.ui.components.dialogs.edit_character_dialog.messagebox.showerror')
def test_on_save_click_empty_name(mock_showerror, dialog):
    """Tests that an empty name prevents saving."""
    dialog.entries[StatType.NAME.value].get.return_value = "" # Empty name
    
    dialog._on_save_click()
    
    mock_showerror.assert_called_once()
    assert "Name cannot be empty" in str(mock_showerror.call_args[0][1])
    dialog.on_save.assert_not_called()
