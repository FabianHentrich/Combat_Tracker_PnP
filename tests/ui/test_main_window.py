import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.ui.main_window import CombatTracker
from src.models.enums import EventType

@pytest.fixture
def app_mocks():
    """Provides a dictionary of all mocked components needed for CombatTracker."""
    with patch('src.ui.main_window.MainView') as MockView, \
         patch('src.ui.main_window.AudioController') as MockAudio, \
         patch('src.ui.main_window.PersistenceHandler') as MockPersistence, \
         patch('src.ui.main_window.CombatEngine') as MockEngine, \
         patch('src.ui.main_window.HotkeyHandler') as MockHotkey, \
         patch('src.ui.main_window.CharacterManagementHandler') as MockChar, \
         patch('src.ui.main_window.CombatActionHandler') as MockCombat, \
         patch('src.ui.main_window.HistoryManager') as MockHistory, \
         patch('src.ui.main_window.ImportHandler') as MockImport, \
         patch('src.ui.main_window.LibraryHandler') as MockLibrary, \
         patch('os.path.exists', return_value=False) as mock_exists, \
         patch('builtins.open', new_callable=mock_open) as mock_open_file, \
         patch('tkinter.messagebox') as mock_messagebox:
        
        yield {
            "view": MockView, "audio": MockAudio, "persistence": MockPersistence,
            "engine": MockEngine, "hotkey": MockHotkey, "char": MockChar,
            "combat": MockCombat, "history": MockHistory, "import": MockImport,
            "library": MockLibrary, "os_exists": mock_exists, "open": mock_open_file,
            "messagebox": mock_messagebox
        }

@pytest.fixture
def tracker(app_mocks):
    """Fixture to create a CombatTracker instance with all dependencies mocked."""
    root = MagicMock()
    # The __init__ of CombatTracker will use the mocked classes
    t = CombatTracker(root)
    return t

# --- Session Save/Load Tests ---

def test_save_session_enriches_state(tracker):
    """Tests that save_session adds audio state before saving."""
    # Mock the return values from the handlers
    tracker.engine.get_state.return_value = {"engine_data": "test"}
    tracker.audio_controller.get_state.return_value = {"audio_data": "test"}
    
    tracker.save_session()
    
    # Verify that persistence_handler.save_session was called with the combined state
    expected_state = {"engine_data": "test", "audio": {"audio_data": "test"}}
    tracker.persistence_handler.save_session.assert_called_once_with(expected_state)

def test_load_session_distributes_state(tracker):
    """Tests that load_session correctly loads data into engine and audio_controller."""
    # Mock the loaded state
    loaded_state = {
        "engine_data": "test", 
        "audio": {"audio_data": "test"},
        "turn_index": 5 # To check if initiative_rolled is set
    }
    tracker.persistence_handler.load_session.return_value = loaded_state
    
    tracker.load_session()
    
    # Verify that the correct parts of the state were passed to the correct components
    tracker.audio_controller.load_state.assert_called_once_with({"audio_data": "test"})
    tracker.engine.load_state.assert_called_once_with(loaded_state)
    
    # Verify that initiative_rolled is set correctly
    assert tracker.engine.initiative_rolled is True

# --- Lifecycle and Autosave Tests ---

def test_autosave_on_update(tracker):
    """Tests that the autosave function is called on an UPDATE event."""
    update_callback = None
    for call in tracker.engine.subscribe.call_args_list:
        if call.args[0] == EventType.UPDATE and "autosave" in str(call.args[1]):
            update_callback = call.args[1]
            break
    
    assert update_callback is not None, "Autosave callback was not subscribed"
    update_callback()
    tracker.persistence_handler.autosave.assert_called_once()

def test_on_closing_removes_lock_file(app_mocks):
    """Tests that the lock file is removed on clean shutdown."""
    app_mocks['os_exists'].return_value = True # Simulate lock file exists
    
    with patch('os.remove') as mock_remove:
        # Re-create tracker inside this context to get the mocked os.remove
        root = MagicMock()
        tracker = CombatTracker(root)
        
        with patch('src.ui.main_window.FILES', {'lock': 'running.lock'}):
            tracker.on_closing()
            mock_remove.assert_called_once_with('running.lock')
            tracker.root.destroy.assert_called_once()
