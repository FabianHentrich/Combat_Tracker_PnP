import pytest
from unittest.mock import MagicMock
import sys
import os

# sys.path.append removed. Run tests with python -m pytest

from src.controllers.import_handler import ImportHandler
from src.models.character import Character

@pytest.fixture
def mock_tracker():
    return MagicMock()

@pytest.fixture
def import_handler(mock_tracker):
    root = MagicMock()
    colors = {"bg": "white", "panel": "grey"}
    engine = MagicMock()
    history_manager = MagicMock()
    return ImportHandler(engine, history_manager, root, colors)

def test_finalize_import(import_handler):
    """
    Testet das Finalisieren des Imports.
    Überprüft, ob Charaktere korrekt aus den Detail-Einträgen erstellt und der Engine hinzugefügt werden.
    """
    # Mock data passed from dialog
    final_data = [{
        "name": "ImportedChar",
        "type": "Gegner",
        "lp": 30,
        "rp": 5,
        "sp": 0,
        "gew": 3
    }]

    import_handler.on_details_confirmed(final_data)

    # Check if insert_character was called
    assert import_handler.engine.insert_character.called
    args, _ = import_handler.engine.insert_character.call_args
    char = args[0]
    assert isinstance(char, Character)
    assert char.name == "ImportedChar"
    assert char.lp == 30
    assert char.rp == 5
    assert char.gew == 3
    assert import_handler.engine.insert_character.called

    # Get the character passed to insert_character
    args, _ = import_handler.engine.insert_character.call_args
    char = args[0]

    assert isinstance(char, Character)
    assert char.name == "ImportedChar"
    assert char.gew == 3
    # Init should be rolled based on gew=3 (which is d8 -> 1-8, but can explode)
    assert char.init >= 1

