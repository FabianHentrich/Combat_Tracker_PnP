import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# sys.path.append removed. Run tests with python -m pytest

from src.controllers.character_management_handler import CharacterManagementHandler
from src.models.character import Character
from src.models.enums import EventType

@pytest.fixture
def mock_tracker():
    tracker = MagicMock()
    return tracker

@pytest.fixture
def char_handler(mock_tracker):
    root = MagicMock()
    colors = {"bg": "white", "panel": "grey"}
    # Mock engine and history_manager
    engine = MagicMock()
    history_manager = MagicMock()
    library_handler = MagicMock()
    view_provider = MagicMock()
    return CharacterManagementHandler(engine, history_manager, view_provider, library_handler, root, colors)

def test_open_edit_window(char_handler):
    """
    Testet, ob das Bearbeiten-Fenster korrekt geöffnet wird.
    """
    char = Character("TestChar", lp=10, rp=5, sp=5, init=10)
    char.id = "uuid-1"

    # Mock _get_selected_char to return our char
    char_handler.engine.get_character_by_id.return_value = char
    char_handler.view.get_selected_char_id.return_value = "uuid-1"

    with patch('src.controllers.character_management_handler.EditCharacterDialog') as MockDialog:
        char_handler.edit_selected_char()

        MockDialog.assert_called_once()
        args, _ = MockDialog.call_args
        assert args[1] == char # char is second arg

def test_save_character_callback(char_handler):
    """
    Testet den Callback zum Speichern von Änderungen.
    """
    char = Character("OldName", lp=10, rp=5, sp=5, init=10, gew=1)

    data = {
        "name": "NewName",
        "char_type": "Spieler",
        "lp": 20,
        "max_lp": 20,
        "rp": 10,
        "max_rp": 10,
        "sp": 10,
        "max_sp": 10,
        "init": 15,
        "gew": 5,
        "status": []
    }

    char_handler._save_character(char, data)

    # Verify update_character was called on engine
    char_handler.engine.update_character.assert_called_once_with(char, data)
    # Verify history snapshot was taken
    char_handler.history_manager.save_snapshot.assert_called_once()
