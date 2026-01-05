import pytest
from unittest.mock import MagicMock, patch
from src.core.turn_manager import TurnManager
from src.models.character import Character
from src.models.enums import ScopeType

@pytest.fixture
def manager():
    """Provides a TurnManager instance with a mocked engine."""
    mock_engine = MagicMock()
    mock_engine.characters = []
    return TurnManager(mock_engine)

# --- Initiative and Combat State Tests ---

@patch('src.core.turn_manager.wuerfle_initiative', return_value=15)
def test_roll_initiatives_starts_combat(mock_wuerfle, manager):
    """Tests that roll_initiatives correctly starts combat."""
    # Character(name, lp, rp, sp, init)
    manager.engine.characters = [Character("A", 10, 0, 0, init=0)]
    
    manager.roll_initiatives()
    
    assert manager.engine.characters[0].init == 15
    assert manager.turn_index == 0
    assert manager.round_number == 1
    assert manager.initiative_rolled is True
    manager.engine.log.assert_any_call("Initiative rolled! Order created.")

def test_reset_initiative(manager):
    """Tests resetting initiative for all characters."""
    manager.engine.characters = [Character("A", 10, 0, 0, init=20)]
    manager.initiative_rolled = True
    manager.turn_index = 0
    
    count = manager.reset_initiative()
    
    assert count == 1
    assert manager.engine.characters[0].init == 0
    assert manager.initiative_rolled is False
    assert manager.turn_index == -1

def test_clear_all_characters_resets_combat(manager):
    """Tests that clearing all characters also resets combat state."""
    manager.engine.characters = [Character("A", 10, 0, 0, 0)]
    manager.turn_index = 0
    
    manager.clear_all_characters()
    
    assert manager.engine.characters == []
    assert manager.turn_index == -1
    assert manager.round_number == 1
    assert manager.initiative_rolled is False

# --- next_turn Tests ---

def test_next_turn_basic_flow(manager):
    """Tests the basic progression of turns."""
    manager.engine.characters = [Character("A", 10, 0, 0, init=20), Character("B", 10, 0, 0, init=10)]
    manager.turn_index = -1
    
    current_char = manager.next_turn()
    assert current_char.name == "A"
    assert manager.turn_index == 0

def test_next_turn_wraps_around(manager):
    """Tests that a new round starts after the last character's turn."""
    manager.engine.characters = [Character("A", 10, 0, 0, 0)]
    manager.turn_index = 0
    manager.round_number = 1
    
    manager.next_turn()
    
    assert manager.round_number == 2

def test_update_character_status_removes_expired(manager):
    """Tests that expired status effects are removed."""
    char = Character("A", 10, 0, 0, 0)
    char.add_status("Poison", 1, 1) # Duration of 1
    
    manager._update_character_status(char)
    
    assert len(char.status) == 0

# --- insert_character Tests ---

def test_insert_character_with_surprise(manager):
    """Tests that a surprise character is inserted at the current turn index."""
    manager.engine.characters = [Character("A", 10, 0, 0, init=20), Character("C", 10, 0, 0, init=10)]
    manager.turn_index = 1
    
    manager.insert_character(Character("B", 10, 0, 0, init=15), surprise=True)
    
    assert [c.name for c in manager.engine.characters] == ["A", "B", "C"]

def test_insert_character_by_initiative(manager):
    """Tests that a character is correctly sorted into the initiative order."""
    manager.engine.characters = [Character("A", 10, 0, 0, init=20), Character("C", 10, 0, 0, init=5)]
    manager.turn_index = 0
    
    manager.insert_character(Character("B", 10, 0, 0, init=15), surprise=False)
    
    assert [c.name for c in manager.engine.characters] == ["A", "B", "C"]
    assert manager.turn_index == 0

# --- remove_character Tests ---

def test_remove_character_before_current(manager):
    """Tests removing a character that is before the current turn."""
    manager.engine.characters = [Character("A", 10, 0, 0, 0), Character("B", 10, 0, 0, 0), Character("C", 10, 0, 0, 0)]
    manager.turn_index = 1
    
    manager.remove_character(0)
    
    assert manager.turn_index == 0

def test_remove_current_character(manager):
    """Tests removing the character whose turn it is."""
    manager.engine.characters = [Character("A", 10, 0, 0, 0), Character("B", 10, 0, 0, 0), Character("C", 10, 0, 0, 0)]
    manager.turn_index = 1
    
    manager.remove_character(1)
    
    assert manager.turn_index == 1
