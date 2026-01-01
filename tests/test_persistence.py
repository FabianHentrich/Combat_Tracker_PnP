import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# sys.path.append removed. Run tests with python -m pytest

# Mocke tkinter Module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from src.core.engine import CombatEngine
from src.models.character import Character
from src.controllers.persistence import PersistenceHandler

@pytest.fixture
def engine():
    return CombatEngine()

def test_character_serialization():
    """
    Testet die Serialisierung und Deserialisierung eines Charakters.
    Überprüft, ob alle Attribute (inkl. Status) korrekt gespeichert und geladen werden.
    """
    c = Character("Hero", 100, 10, 5, 20, gew=3, char_type="Spieler")
    c.add_status("Vergiftung", 3, 2)

    data = c.to_dict()

    assert data["name"] == "Hero"
    assert data["lp"] == 100
    assert data["status"][0]["effect"] == "Vergiftung"

    c2 = Character.from_dict(data)
    assert c2.name == c.name
    assert c2.lp == c.lp
    assert c2.status[0].name == "Vergiftung"
    assert c2.status[0].duration == 3

def test_engine_state_serialization(engine):
    """
    Testet die Serialisierung des gesamten Engine-Zustands.
    Überprüft, ob Charakterliste, Turn-Index und Rundennummer korrekt gespeichert werden.
    """
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    engine.characters = [c1, c2]
    engine.turn_index = 1
    engine.round_number = 5

    state = engine.get_state()

    assert len(state["characters"]) == 2
    assert state["turn_index"] == 1
    assert state["round_number"] == 5

    # Create new engine and load state
    engine2 = CombatEngine()
    engine2.load_state(state)

    assert len(engine2.characters) == 2
    assert engine2.characters[0].name == "A"
    assert engine2.turn_index == 1
    assert engine2.round_number == 5

def test_persistence_handler_save():
    """
    Testet das Speichern der Session über den PersistenceHandler.
    Überprüft, ob der Dateidialog aufgerufen und in die Datei geschrieben wird.
    """
    state = {"some": "state"}
    handler = PersistenceHandler(MagicMock())

    # Patch where it is used
    with patch('src.controllers.persistence.filedialog.asksaveasfilename', return_value="test.json"):
        with patch('builtins.open', mock_open()) as m:
            handler.save_session(state)

            m.assert_called_once_with("test.json", 'w', encoding='utf-8')
            handle = m()
            # Check if write was called
            assert handle.write.called

def test_persistence_handler_load():
    """
    Testet das Laden der Session über den PersistenceHandler.
    Überprüft, ob der Dateidialog aufgerufen und die Daten in die Engine geladen werden.
    """
    handler = PersistenceHandler(MagicMock())

    state_data = {
        "version": 1,
        "state": {
            "characters": [],
            "turn_index": -1,
            "round_number": 1
        }
    }
    json_str = json.dumps(state_data)

    with patch('src.controllers.persistence.filedialog.askopenfilename', return_value="test.json"):
        with patch('builtins.open', mock_open(read_data=json_str)):
            loaded_state = handler.load_session()

            assert loaded_state == state_data["state"]


