import pytest
from unittest.mock import MagicMock, patch
from src.controllers.persistence import PersistenceHandler

@pytest.fixture
def handler():
    """Fixture to create a PersistenceHandler instance with a mocked root."""
    mock_root = MagicMock()
    return PersistenceHandler(mock_root)

# --- save_session Tests ---

@patch('src.controllers.persistence.SaveManager.save_to_file')
@patch('src.controllers.persistence.filedialog.asksaveasfilename', return_value="test.json")
def test_save_session_success(mock_asksaveasfilename, mock_save_to_file, handler):
    """Tests the successful save workflow."""
    state = {"data": "test"}
    result = handler.save_session(state)
    
    mock_asksaveasfilename.assert_called_once()
    mock_save_to_file.assert_called_once_with("test.json", state)
    assert result == "test.json"

@patch('src.controllers.persistence.filedialog.asksaveasfilename', return_value="")
def test_save_session_user_cancel(mock_asksaveasfilename, handler):
    """Tests that nothing happens if the user cancels the save dialog."""
    result = handler.save_session({})
    mock_asksaveasfilename.assert_called_once()
    assert result is None

@patch('src.controllers.persistence.messagebox.showerror')
@patch('src.controllers.persistence.SaveManager.save_to_file', side_effect=IOError("Disk full"))
@patch('src.controllers.persistence.filedialog.asksaveasfilename', return_value="test.json")
def test_save_session_exception(mock_asksaveasfilename, mock_save_to_file, mock_showerror, handler):
    """Tests that an error message is shown if saving fails."""
    result = handler.save_session({})
    mock_showerror.assert_called_once_with("Error", "Disk full")
    assert result is None

# --- load_session Tests ---

@patch('src.controllers.persistence.SaveManager.load_from_file', return_value={"data": "test"})
@patch('src.controllers.persistence.filedialog.askopenfilename', return_value="test.json")
def test_load_session_success(mock_askopenfilename, mock_load_from_file, handler):
    """Tests the successful load workflow."""
    result = handler.load_session()
    
    mock_askopenfilename.assert_called_once()
    mock_load_from_file.assert_called_once_with("test.json")
    assert result == {"data": "test"}

@patch('src.controllers.persistence.filedialog.askopenfilename', return_value="")
def test_load_session_user_cancel(mock_askopenfilename, handler):
    """Tests that nothing happens if the user cancels the load dialog."""
    result = handler.load_session()
    mock_askopenfilename.assert_called_once()
    assert result is None

@patch('src.controllers.persistence.messagebox.showerror')
@patch('src.controllers.persistence.SaveManager.load_from_file', side_effect=IOError("File not found"))
@patch('src.controllers.persistence.filedialog.askopenfilename', return_value="test.json")
def test_load_session_exception(mock_askopenfilename, mock_load_from_file, mock_showerror, handler):
    """Tests that an error message is shown if loading fails."""
    result = handler.load_session()
    mock_showerror.assert_called_once_with("Error", "File not found")
    assert result is None

# --- Autosave Tests ---

@patch('src.controllers.persistence.SaveManager.save_to_file')
@patch('src.controllers.persistence.FILES', {"autosave": "autosave.json"})
def test_autosave(mock_save_to_file, handler):
    """Tests that autosave calls the save manager with the correct file path."""
    state = {"data": "autosave_test"}
    handler.autosave(state)
    mock_save_to_file.assert_called_once_with("autosave.json", state)

@patch('src.controllers.persistence.SaveManager.load_from_file', return_value={"data": "test"})
@patch('src.controllers.persistence.FILES', {"autosave": "autosave.json"})
def test_load_autosave_success(mock_load_from_file, handler):
    """Tests the successful loading of an autosave file."""
    result = handler.load_autosave()
    mock_load_from_file.assert_called_once_with("autosave.json")
    assert result == {"data": "test"}

@patch('src.controllers.persistence.SaveManager.load_from_file', side_effect=FileNotFoundError)
@patch('src.controllers.persistence.FILES', {"autosave": "autosave.json"})
def test_load_autosave_not_found(mock_load_from_file, handler):
    """Tests that load_autosave returns None if the file doesn't exist."""
    result = handler.load_autosave()
    assert result is None
