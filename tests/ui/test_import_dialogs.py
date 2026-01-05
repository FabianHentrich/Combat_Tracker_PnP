import pytest
from unittest.mock import patch, MagicMock
from src.ui.components.dialogs.import_dialogs import ImportPreviewDialog, ImportDetailDialog
from src.models.enums import StatType, CharacterType

@pytest.fixture
def mock_root():
    """Provides a mock Tk root window."""
    return MagicMock()

@pytest.fixture
def colors():
    """Provides a sample color dictionary."""
    return {"bg": "white", "fg": "black", "panel": "grey"}

# --- Helper to mock a dialog's UI setup ---
@pytest.fixture
def mock_dialog_ui():
    with patch('src.ui.components.dialogs.import_dialogs.tk.Toplevel'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Frame'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Label'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Entry'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Combobox'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Button'), \
         patch('src.ui.components.dialogs.import_dialogs.tk.Canvas'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Scrollbar'):
        yield

# --- ImportPreviewDialog Tests ---

def test_import_preview_dialog_on_next(mock_root, colors, mock_dialog_ui):
    """Tests the data expansion logic of the 'Next' button."""
    data = [{"Name": "Orc", "HP": 15, "Ruestung": 2, "Schild": 0, "Gewandtheit": 1}]
    confirm_callback = MagicMock()

    dialog = ImportPreviewDialog(mock_root, data, colors, confirm_callback)
    
    # Manually mock the entry widgets created by the (patched) UI setup
    mock_entry = {
        "name": MagicMock(get=MagicMock(return_value="Orc")),
        "type": MagicMock(get=MagicMock(return_value="Enemy")),
        "lp": MagicMock(get=MagicMock(return_value="15")),
        "rp": MagicMock(get=MagicMock(return_value="2")),
        "sp": MagicMock(get=MagicMock(return_value="0")),
        "gew": MagicMock(get=MagicMock(return_value="1")),
        "level": MagicMock(get=MagicMock(return_value="1")),
        "count": MagicMock(get=MagicMock(return_value="2")) # User wants 2 Orcs
    }
    dialog.import_entries = [mock_entry]
    dialog.translated_types = {"Enemy": "ENEMY"}
    dialog.window = MagicMock() # Mock the window to check destroy()

    dialog._on_next()

    confirm_callback.assert_called_once()
    call_args = confirm_callback.call_args[0][0]
    
    assert len(call_args) == 2
    assert call_args[0][StatType.NAME.value] == "Orc 1"
    assert call_args[1][StatType.NAME.value] == "Orc 2"
    dialog.window.destroy.assert_called_once()

@patch('src.ui.components.dialogs.import_dialogs.messagebox.showerror')
def test_import_preview_dialog_on_next_value_error(mock_showerror, mock_root, colors, mock_dialog_ui):
    """Tests that an error is shown if 'count' is not a valid number."""
    data = [{"Name": "Orc", "HP": 15, "Ruestung": 2, "Schild": 0, "Gewandtheit": 1}]
    confirm_callback = MagicMock()
    dialog = ImportPreviewDialog(mock_root, data, colors, confirm_callback)
    
    mock_entry = {"count": MagicMock(get=MagicMock(return_value="abc"))}
    dialog.import_entries = [mock_entry]

    dialog._on_next()
    
    mock_showerror.assert_called_once()
    confirm_callback.assert_not_called()

# --- ImportDetailDialog Tests ---

def test_import_detail_dialog_on_finish_success(mock_root, colors, mock_dialog_ui):
    """Tests the successful data collection of the 'Finish' button."""
    data = [] # Initial data is empty as the dialog is populated manually in the test
    finish_callback = MagicMock()
    dialog = ImportDetailDialog(mock_root, data, colors, finish_callback)
    
    # Manually create a mock entry as if it were created by the UI
    mock_entry = {
        "name": MagicMock(get=MagicMock(return_value="Final Orc")),
        "type": MagicMock(get=MagicMock(return_value="Enemy")),
        "lp": MagicMock(get=MagicMock(return_value="20")),
        "rp": MagicMock(get=MagicMock(return_value="5")),
        "sp": MagicMock(get=MagicMock(return_value="0")),
        "gew": MagicMock(get=MagicMock(return_value="1")),
        "level": MagicMock(get=MagicMock(return_value="3"))
    }
    dialog.detail_entries = [mock_entry]
    dialog.translated_types = {"Enemy": "ENEMY"}
    dialog.window = MagicMock()

    dialog._on_finish()

    finish_callback.assert_called_once()
    final_data = finish_callback.call_args[0][0]
    
    assert len(final_data) == 1
    assert final_data[0][StatType.NAME.value] == "Final Orc"
    assert final_data[0][StatType.LP.value] == 20
    assert final_data[0][StatType.TYPE.value] == "ENEMY"
    dialog.window.destroy.assert_called_once()

@patch('src.ui.components.dialogs.import_dialogs.messagebox.showerror')
def test_import_detail_dialog_on_finish_value_error(mock_showerror, mock_root, colors, mock_dialog_ui):
    """Tests that an error is shown if final data is not a valid number."""
    data = []
    finish_callback = MagicMock()
    dialog = ImportDetailDialog(mock_root, data, colors, finish_callback)
    
    mock_entry = {
        "name": MagicMock(get=MagicMock(return_value="Invalid Orc")),
        "type": MagicMock(get=MagicMock(return_value="Enemy")),
        "lp": MagicMock(get=MagicMock(return_value="abc")), # Invalid LP
        "rp": MagicMock(), "sp": MagicMock(), "gew": MagicMock(), "level": MagicMock()
    }
    dialog.detail_entries = [mock_entry]
    dialog.translated_types = {"Enemy": "ENEMY"}

    dialog._on_finish()
    
    mock_showerror.assert_called_once_with("Error", "Please use valid numbers for stats.")
    finish_callback.assert_not_called()
