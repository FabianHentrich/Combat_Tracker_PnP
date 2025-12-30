import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.import_handler import ImportHandler
from src.character import Character

@pytest.fixture
def mock_tracker():
    return MagicMock()

@pytest.fixture
def import_handler(mock_tracker):
    root = MagicMock()
    colors = {"bg": "white", "panel": "grey"}
    return ImportHandler(mock_tracker, root, colors)

def test_finalize_import(import_handler):
    """Test finalizing import creates characters correctly."""
    window = MagicMock()

    # Mock detail entry
    entry_mock = {
        "name": MagicMock(),
        "type": MagicMock(),
        "lp": MagicMock(),
        "rp": MagicMock(),
        "sp": MagicMock(),
        "gew": MagicMock()
    }

    entry_mock["name"].get.return_value = "ImportedChar"
    entry_mock["type"].get.return_value = "Gegner"
    entry_mock["lp"].get.return_value = "30"
    entry_mock["rp"].get.return_value = "5"
    entry_mock["sp"].get.return_value = "0"
    entry_mock["gew"].get.return_value = "3"

    import_handler.detail_entries = [entry_mock]

    import_handler.finalize_import(window)

    # Check if insert_character was called
    assert import_handler.tracker.insert_character.called

    # Get the character passed to insert_character
    args, _ = import_handler.tracker.insert_character.call_args
    char = args[0]

    assert isinstance(char, Character)
    assert char.name == "ImportedChar"
    assert char.gew == 3
    # Init should be rolled based on gew=3 (which is d8 -> 1-8, but can explode)
    assert char.init >= 1

    window.destroy.assert_called_once()

