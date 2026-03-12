import pytest
from unittest.mock import MagicMock, patch, ANY
from src.controllers.import_handler import ImportHandler
from src.models.character import Character

@pytest.fixture
def handler():
    """Fixture to create an ImportHandler instance with mocked dependencies."""
    mock_engine = MagicMock(spec=["insert_character", "log"])
    mock_history = MagicMock(spec=["save_snapshot"])
    mock_root = MagicMock()
    mock_colors = {}
    return ImportHandler(mock_engine, mock_history, mock_root, mock_colors)

@pytest.fixture
def mock_workbook():
    """Creates a mocked openpyxl Workbook with standard data."""
    mock_sheet = MagicMock()
    header = [MagicMock(value=h) for h in ["Name", "HP", "Ruestung", "Schild", "Gewandtheit"]]
    
    mock_sheet.iter_rows.return_value = [
        ("Goblin", 10, 2, 0, 2),
        ("Orc", 25, 5, 0, 1)
    ]
    mock_sheet.__getitem__.return_value = header

    mock_wb = MagicMock()
    mock_wb.active = mock_sheet
    return mock_wb

# --- load_from_excel Tests ---

def test_load_from_excel_user_cancel(handler):
    """Tests that the function exits gracefully if the user cancels the file dialog."""
    with patch('src.controllers.import_handler.filedialog.askopenfilename', return_value="") as mock_file_dialog:
        handler.load_from_excel()
        mock_file_dialog.assert_called_once()
        # Ensure no further processing happens
        handler.history_manager.save_snapshot.assert_called_once() # Snapshot is saved before dialog
        handler.engine.insert_character.assert_not_called()

@patch('src.controllers.import_handler.ImportPreviewDialog')
@patch('src.controllers.import_handler.filedialog.askopenfilename', return_value="dummy.xlsx")
@patch('src.controllers.import_handler.openpyxl.load_workbook')
def test_load_from_excel_skips_empty_rows(mock_load_wb, mock_file_dialog, MockPreviewDialog, handler, mock_workbook):
    """Tests that rows with no name are skipped."""
    # Add an empty row to the mock data
    mock_sheet = mock_workbook.active
    mock_sheet.iter_rows.return_value = [
        ("Goblin", 10, 2, 0, 2),
        (None, 50, 5, 5, 5), # This row should be skipped
        ("Orc", 25, 5, 0, 1)
    ]
    mock_load_wb.return_value = mock_workbook

    handler.load_from_excel()

    # The data passed to the preview dialog should not contain the empty row
    expected_data = [
        {'Name': 'Goblin', 'HP': 10, 'Ruestung': 2, 'Schild': 0, 'Gewandtheit': 2},
        {'Name': 'Orc', 'HP': 25, 'Ruestung': 5, 'Schild': 0, 'Gewandtheit': 1}
    ]
    MockPreviewDialog.assert_called_once_with(handler.root, expected_data, handler.colors, ANY)

def test_load_from_excel_missing_columns(handler):
    """Tests that an error is shown if required columns are missing."""
    mock_sheet = MagicMock()
    header = [MagicMock(value="Name"), MagicMock(value="Ruestung")] # HP is missing
    mock_sheet.__getitem__.return_value = header
    mock_wb = MagicMock()
    mock_wb.active = mock_sheet

    with patch('src.controllers.import_handler.openpyxl.load_workbook', return_value=mock_wb), \
         patch('src.controllers.import_handler.filedialog.askopenfilename', return_value="bad.xlsx"), \
         patch('src.controllers.import_handler.messagebox.showerror') as mock_showerror:
        
        handler.load_from_excel()
        
        mock_showerror.assert_called_once()
        assert "missing columns" in mock_showerror.call_args[0][1]

# --- Callback and Finalization Tests ---

@patch('src.controllers.import_handler.ImportDetailDialog')
def test_on_preview_confirmed_empty_data(MockDetailDialog, handler):
    """Tests that the detail dialog is not opened if preview data is empty."""
    handler.on_preview_confirmed([])
    MockDetailDialog.assert_not_called()

def test_on_details_confirmed_imports_characters(handler):
    """Tests the successful import of characters from final data."""
    final_data = [
        {'name': 'Goblin', 'type': 'Gegner', 'lp': 10, 'rp': 2, 'sp': 0, 'gew': 2, 'level': 1},
        {'name': 'Orc', 'type': 'Gegner', 'lp': 25, 'rp': 5, 'sp': 0, 'gew': 1, 'level': 3}
    ]

    with patch('src.controllers.import_handler.wuerfle_initiative', return_value=15):
        handler.on_details_confirmed(final_data)

    assert handler.engine.insert_character.call_count == 2
    handler.engine.log.assert_called_with("2 characters imported successfully.")

@patch('src.controllers.import_handler.MAX_GEW', 5)
def test_on_details_confirmed_caps_gew(handler):
    """Tests that Gewandtheit is capped at MAX_GEW during import."""
    final_data = [{'name': 'Speedy', 'type': 'Gegner', 'lp': 10, 'rp': 0, 'sp': 0, 'gew': 8, 'level': 1}]
    
    with patch('src.controllers.import_handler.wuerfle_initiative'):
        handler.on_details_confirmed(final_data)
    
    handler.engine.insert_character.assert_called_once()
    inserted_char = handler.engine.insert_character.call_args[0][0]
    assert inserted_char.gew == 5 # Should be capped to 5

@patch('src.controllers.import_handler.messagebox.showerror')
def test_on_details_confirmed_handles_key_error(mock_showerror, handler):
    """Tests that an error is shown if the final data is missing a required key."""
    # Data is missing the 'lp' key
    final_data = [{'name': 'Incomplete', 'type': 'Gegner', 'rp': 0, 'sp': 0, 'gew': 1, 'level': 1}]
    
    handler.on_details_confirmed(final_data)
    
    mock_showerror.assert_called_once()
    assert "Error during import" in mock_showerror.call_args[0][1]
    handler.engine.insert_character.assert_not_called()
