import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock tkinter globally
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

from src.ui.main_window import CombatTracker
from src.models.enums import EventType

@pytest.fixture
def mock_tracker():
    with patch('src.ui.main_window.MainView'), \
         patch('src.ui.main_window.AudioController'), \
         patch('src.ui.main_window.PersistenceHandler') as MockPersistence:

        root = MagicMock()
        tracker = CombatTracker(root)
        # Ensure persistence handler is the mock we expect
        tracker.persistence_handler = MockPersistence.return_value
        yield tracker

def test_autosave_triggered_on_update(mock_tracker):
    """Testet, ob das Autosave bei einem UPDATE-Event ausgelöst wird."""
    # Reset mock to clear calls from init
    mock_tracker.persistence_handler.autosave.reset_mock()

    # Simulate an engine update (e.g. character added, damage dealt)
    mock_tracker.engine.notify(EventType.UPDATE)

    # Verify autosave was called
    mock_tracker.persistence_handler.autosave.assert_called_once()

def test_autosave_crash_recovery():
    """Testet, ob bei einem Absturz (Lock-Datei existiert) der Autosave geladen wird."""
    with patch('src.ui.main_window.MainView'), \
         patch('src.ui.main_window.AudioController'), \
         patch('src.ui.main_window.PersistenceHandler') as MockPersistence, \
         patch('os.path.exists', return_value=True), \
         patch('tkinter.messagebox.askyesno', return_value=True): # User says YES

        root = MagicMock()
        tracker = CombatTracker(root)

        # Verify load_autosave was called
        tracker.persistence_handler.load_autosave.assert_called_once()

def test_autosave_normal_startup():
    """Testet, ob bei normalem Start (keine Lock-Datei) der Autosave NICHT geladen wird."""
    with patch('src.ui.main_window.MainView'), \
         patch('src.ui.main_window.AudioController'), \
         patch('src.ui.main_window.PersistenceHandler') as MockPersistence, \
         patch('os.path.exists', return_value=False), \
         patch('builtins.open', new_callable=MagicMock): # Mock file creation

        root = MagicMock()
        tracker = CombatTracker(root)

        # Verify load_autosave was NOT called
        tracker.persistence_handler.load_autosave.assert_not_called()
