import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# sys.path.append removed. Run tests with python -m pytest

from src.controllers.edit_handler import EditHandler
from src.models.character import Character
from src.models.enums import EventType

@pytest.fixture
def mock_tracker():
    tracker = MagicMock()
    return tracker

@pytest.fixture
def edit_handler(mock_tracker):
    root = MagicMock()
    colors = {"bg": "white", "panel": "grey"}
    # Mock engine and history_manager
    engine = MagicMock()
    history_manager = MagicMock()
    return EditHandler(engine, history_manager, root, colors)

def test_status_effect_is_label(edit_handler):
    """
    Testet, ob der Name eines Status-Effekts im Bearbeiten-Fenster als Label (nicht editierbar) angezeigt wird.
    """

    char = Character("TestChar", lp=10, rp=5, sp=5, init=10)
    char.add_status("Vergiftung", 3, 1)

    with patch('src.controllers.edit_handler.tk.Toplevel') as MockToplevel, \
         patch('src.controllers.edit_handler.ttk.Frame') as MockFrame, \
         patch('src.controllers.edit_handler.ttk.Entry') as MockEntry, \
         patch('src.controllers.edit_handler.ttk.Label') as MockLabel, \
         patch('src.controllers.edit_handler.ttk.Button') as MockButton, \
         patch('src.controllers.edit_handler.ttk.Combobox') as MockCombobox, \
         patch('src.controllers.edit_handler.ttk.Separator') as MockSeparator:

        edit_handler.open_edit_character_window(char)

        # Check if a Label was created with text="Vergiftung"
        # MockLabel is called multiple times. We need to check call_args_list.

        found = False
        for call in MockLabel.call_args_list:
            # call.kwargs contains 'text'
            if call.kwargs.get('text') == "Vergiftung":
                found = True
                break

        assert found, "Could not find a Label with text='Vergiftung'"

def test_save_character_edits(edit_handler):
    """
    Testet das Speichern von Änderungen an einem Charakter, einschließlich neuer Felder wie 'gew'.
    Überprüft, ob die Werte im Charakter-Objekt aktualisiert werden.
    """
    char = Character("OldName", lp=10, rp=5, sp=5, init=10, gew=1)
    window = MagicMock()

    # Mock entries
    entries = {
        "name": MagicMock(),
        "type": MagicMock(),
        "lp": MagicMock(),
        "max_lp": MagicMock(),
        "rp": MagicMock(),
        "max_rp": MagicMock(),
        "sp": MagicMock(),
        "max_sp": MagicMock(),
        "init": MagicMock(),
        "gew": MagicMock()
    }

    # Setup return values
    entries["name"].get.return_value = "NewName"
    entries["type"].get.return_value = "Spieler"
    entries["lp"].get.return_value = "20"
    entries["max_lp"].get.return_value = "20"
    entries["rp"].get.return_value = "10"
    entries["max_rp"].get.return_value = "10"
    entries["sp"].get.return_value = "10"
    entries["max_sp"].get.return_value = "10"
    entries["init"].get.return_value = "15"
    entries["gew"].get.return_value = "5"

    # Mock status entries
    status_ui_entries = [] # Empty for simplicity

    edit_handler.save_character_edits(window, char, entries, status_ui_entries)

    # Assertions
    assert char.name == "NewName"
    assert char.char_type == "Spieler"
    assert char.lp == 20
    assert char.init == 15
    assert char.gew == 5 # Check if gew was updated

    edit_handler.engine.notify.assert_called_with(EventType.UPDATE)
    window.destroy.assert_called_once()
