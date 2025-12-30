import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocke tkinter Module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from src.engine import CombatEngine
from src.character import Character
from src.persistence import PersistenceHandler

@pytest.fixture
def engine():
    return CombatEngine()

def test_character_serialization():
    c = Character("Hero", 100, 10, 5, 20, gew=3, char_type="Spieler")
    c.add_status("Vergiftung", 3, 2)

    data = c.to_dict()

    assert data["name"] == "Hero"
    assert data["lp"] == 100
    assert data["status"][0]["effect"] == "Vergiftung"

    c2 = Character.from_dict(data)
    assert c2.name == c.name
    assert c2.lp == c.lp
    assert c2.status[0]["effect"] == "Vergiftung"
    assert c2.status[0]["rounds"] == 3

def test_engine_state_serialization(engine):
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
    tracker = MagicMock()
    tracker.engine = CombatEngine()
    tracker.engine.add_character(Character("Test", 10, 10, 10, 10))

    handler = PersistenceHandler(tracker, MagicMock())

    # Patch where it is used
    with patch('src.persistence.filedialog.asksaveasfilename', return_value="test.json"):
        with patch('builtins.open', mock_open()) as m:
            handler.save_session()

            m.assert_called_once_with("test.json", 'w', encoding='utf-8')
            handle = m()
            # Check if write was called
            assert handle.write.called

def test_persistence_handler_load():
    tracker = MagicMock()
    tracker.engine = CombatEngine()

    handler = PersistenceHandler(tracker, MagicMock())

    state_data = {
        "characters": [
            {"name": "Loaded", "char_type": "Gegner", "max_lp": 10, "lp": 10, "max_rp": 0, "rp": 0, "max_sp": 0, "sp": 0, "gew": 1, "init": 10, "status": [], "skip_turns": 0}
        ],
        "turn_index": 0,
        "round_number": 2
    }
    json_str = json.dumps(state_data)

    # Patch where it is used
    with patch('src.persistence.filedialog.askopenfilename', return_value="test.json"):
        with patch('builtins.open', mock_open(read_data=json_str)):
            handler.load_session()

            assert len(tracker.engine.characters) == 1
            assert tracker.engine.characters[0].name == "Loaded"
            assert tracker.engine.round_number == 2
            assert tracker.update_listbox.called

