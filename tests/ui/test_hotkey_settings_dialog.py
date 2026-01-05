import pytest
from unittest.mock import MagicMock, patch

# Mock tkinter before import
@patch('tkinter.Toplevel')
def get_hotkey_dialog(MockToplevel):
    from src.ui.components.dialogs.hotkey_settings_dialog import HotkeySettingsDialog
    
    mock_parent = MagicMock()
    mock_hotkeys = {"next_turn": "<space>"}
    mock_colors = {"bg": "black"}
    mock_on_save = MagicMock()
    
    with patch.object(HotkeySettingsDialog, '_setup_ui'):
        dialog = HotkeySettingsDialog(mock_parent, mock_hotkeys, mock_colors, mock_on_save)
        dialog.window = MockToplevel()
        
    return dialog

@pytest.fixture
def dialog():
    """Provides a HotkeySettingsDialog instance with mocked UI elements."""
    return get_hotkey_dialog()

# --- _get_hotkey_string_from_event Tests ---

def test_get_hotkey_string_from_event(dialog):
    """Tests the conversion of tk.Event to a hotkey string."""
    event = MagicMock()
    
    # Simple key
    event.keysym = "a"
    event.state = 0
    assert dialog._get_hotkey_string_from_event(event) == "<a>"
    
    # Control + key
    event.keysym = "z"
    event.state = 0x0004 # Control mask
    assert dialog._get_hotkey_string_from_event(event) == "<Control-z>"
    
    # Control + Shift + key
    event.keysym = "Y"
    event.state = 0x0004 | 0x0001 # Control + Shift
    assert dialog._get_hotkey_string_from_event(event) == "<Control-Shift-Y>"
    
    # Function key
    event.keysym = "F5"
    event.state = 0
    assert dialog._get_hotkey_string_from_event(event) == "<F5>"
    
    # Ignored modifier key
    event.keysym = "Control_L"
    assert dialog._get_hotkey_string_from_event(event) is None

# --- _start_listening Test ---

def test_start_listening_flow(dialog):
    """Tests the process of listening for and setting a new hotkey."""
    mock_button = MagicMock()
    key_name_to_change = "next_turn"
    
    # 1. Start listening
    dialog._start_listening(key_name_to_change, mock_button)
    
    # Check that UI is updated to show "Press a key..."
    mock_button.configure.assert_called_with(text="Press a key...")
    # Check that the event is bound
    dialog.window.bind.assert_called_with("<Key>", unittest.mock.ANY)
    
    # 2. Simulate a key press event
    # Extract the callback function that was bound
    on_key_callback = dialog.window.bind.call_args[0][1]
    
    mock_event = MagicMock()
    mock_event.keysym = "p"
    mock_event.state = 0x0004 # Control
    
    on_key_callback(mock_event)
    
    # 3. Verify the results
    # Check that the new hotkey was stored
    assert dialog.hotkeys[key_name_to_change] == "<Control-p>"
    # Check that the button text was updated
    mock_button.configure.assert_called_with(text="<Control-p>")
    # Check that the event listener was unbound
    dialog.window.unbind.assert_called_with("<Key>")

# --- _on_save Test ---

def test_on_save(dialog):
    """Tests that the on_save callback is called with the modified hotkeys."""
    # Modify the hotkeys dictionary
    dialog.hotkeys["next_turn"] = "<F1>"
    dialog.hotkeys["undo"] = "<Control-u>"
    
    dialog._on_save()
    
    # Check that the callback was called with the correct, modified dictionary
    dialog.on_save.assert_called_once_with({
        "next_turn": "<F1>",
        "undo": "<Control-u>"
    })
    
    # Check that the window was destroyed
    dialog.window.destroy.assert_called_once()
