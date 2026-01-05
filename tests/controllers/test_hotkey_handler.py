import pytest
from unittest.mock import MagicMock, patch, mock_open, ANY
import tkinter as tk
from src.controllers.hotkey_handler import HotkeyHandler

@pytest.fixture
def handler():
    """Provides a HotkeyHandler instance with a mock root."""
    root = MagicMock()
    root.focus_get.return_value = None
    return HotkeyHandler(root, colors={"bg": "#FFF", "fg": "#000"})

# --- Tests ---

@patch('src.controllers.hotkey_handler.messagebox')
@patch('src.controllers.hotkey_handler.json.dump')
@patch('src.controllers.hotkey_handler.open', new_callable=mock_open)
@patch('src.controllers.hotkey_handler.HOTKEYS', {})
@patch('src.controllers.hotkey_handler.FILES', {"hotkeys": "dummy_path.json"})
def test_save_hotkeys_success(mock_open_file, mock_json_dump, mock_messagebox, handler):
    """Tests the successful saving and reloading of hotkeys without blocking."""
    new_hotkeys = {"next_turn": "<F1>"}
    handler.settings_dialog = MagicMock()

    # Patch the instance method directly using a context manager for robustness
    with patch.object(handler, '_bind_keys') as mock_bind:
        handler.save_hotkeys(new_hotkeys)

        mock_open_file.assert_called_with("dummy_path.json", 'w', encoding='utf-8')
        mock_json_dump.assert_called_with(new_hotkeys, mock_open_file(), indent=4)
        mock_bind.assert_called_once()
        handler.settings_dialog.destroy.assert_called_once()
        mock_messagebox.showinfo.assert_called_once()

def test_setup_hotkeys(handler):
    """Tests that hotkeys are correctly bound."""
    callbacks = {"next_turn": MagicMock()}
    with patch('src.controllers.hotkey_handler.HOTKEYS', {"next_turn": "<F1>"}):
        handler.setup_hotkeys(callbacks)
        # Check that root.bind was called with the correct hotkey and ANY callable
        handler.root.bind.assert_called_once_with("<F1>", ANY)

@patch('src.controllers.hotkey_handler.isinstance', return_value=False)
def test_safe_execute_no_focus(mock_isinstance, handler):
    """Tests that the callback is executed when the focused widget is not an input field."""
    callback = MagicMock()
    event = MagicMock(keysym='a')
    handler.safe_execute(event, callback)
    callback.assert_called_once()
    mock_isinstance.assert_called_once()

@patch('src.controllers.hotkey_handler.isinstance', return_value=True)
def test_safe_execute_input_focus(mock_isinstance, handler):
    """Tests that the callback is NOT executed when an Entry has focus."""
    callback = MagicMock()
    event = MagicMock(keysym='a')
    
    handler.safe_execute(event, callback)
    
    callback.assert_not_called()
    mock_isinstance.assert_called_once()

def test_safe_execute_non_char_key(handler):
    """Tests that the callback IS executed for non-character keys (like F-keys) even with focus."""
    callback = MagicMock()
    event = MagicMock(keysym='F1') # A non-character key
    
    # This test doesn't need to patch isinstance because the first part of the 'if' condition
    # `is_char_key` will be False, short-circuiting the evaluation.
    handler.safe_execute(event, callback)
    
    callback.assert_called_once()
