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


# --- sort_initiative / roll_all_initiatives ---

def test_sort_initiative_orders_descending(manager):
    """Tests that sort_initiative sorts characters by init descending."""
    manager.engine.characters = [
        Character("Low", 10, 0, 0, init=5),
        Character("High", 10, 0, 0, init=20),
        Character("Mid", 10, 0, 0, init=10),
    ]
    manager.sort_initiative()
    names = [c.name for c in manager.engine.characters]
    assert names == ["High", "Mid", "Low"]

@patch('src.core.turn_manager.wuerfle_initiative', return_value=8)
def test_roll_all_initiatives_rerolls_everyone(mock_wuerfle, manager):
    """Tests that roll_all_initiatives rerolls for every character."""
    manager.engine.characters = [
        Character("A", 10, 0, 0, init=20),
        Character("B", 10, 0, 0, init=15),
    ]
    manager.roll_all_initiatives()
    # All should now have the mocked value
    assert all(c.init == 8 for c in manager.engine.characters)
    assert mock_wuerfle.call_count == 2


# --- next_turn edge cases ---

def test_next_turn_returns_none_with_no_characters(manager):
    """Tests that next_turn returns None when there are no characters."""
    manager.engine.characters = []
    result = manager.next_turn()
    assert result is None

def test_next_turn_logs_incapacitated_character(manager):
    """Tests that a character with 0 LP gets an incapacitated log line."""
    dead_char = Character("Fallen", lp=0, rp=0, sp=0, init=10)
    manager.engine.characters = [dead_char]
    manager.turn_index = -1
    manager.next_turn()
    # The log call should mention the character's name with incapacitated message
    log_calls = [str(call) for call in manager.engine.log.call_args_list]
    assert any("Fallen" in c for c in log_calls)

def test_next_turn_skips_stunned_character(manager):
    """Tests that a stunned character (skip_turns=1) is skipped over."""
    stunned = Character("Stunned", 10, 0, 0, init=20)
    normal = Character("Normal", 10, 0, 0, init=10)
    manager.engine.characters = [stunned, normal]
    manager.turn_index = -1

    # Simulate StunEffect already having set skip_turns
    stunned.skip_turns = 1
    # Patch _update_character_status so it doesn't reset skip_turns to 0 before we check
    with patch.object(manager, '_update_character_status'):
        result = manager.next_turn()

    # After skipping stunned, should return Normal
    assert result.name == "Normal"


# --- remove_characters_by_type ---

def test_remove_characters_by_type(manager):
    """Tests that only characters of the given type are removed."""
    from src.models.enums import CharacterType
    enemy = Character("Goblin", 10, 0, 0, 0)
    enemy.char_type = CharacterType.ENEMY
    player = Character("Hero", 10, 0, 0, 0)
    player.char_type = CharacterType.PLAYER
    manager.engine.characters = [enemy, player]
    manager.turn_index = 0

    manager.remove_characters_by_type(CharacterType.ENEMY)

    assert len(manager.engine.characters) == 1
    assert manager.engine.characters[0].name == "Hero"

def test_remove_characters_by_type_clamps_turn_index(manager):
    """Tests that turn_index is clamped after bulk removal."""
    from src.models.enums import CharacterType
    enemy1 = Character("A", 10, 0, 0, 0)
    enemy1.char_type = CharacterType.ENEMY
    enemy2 = Character("B", 10, 0, 0, 0)
    enemy2.char_type = CharacterType.ENEMY
    manager.engine.characters = [enemy1, enemy2]
    manager.turn_index = 1  # Beyond the list after removal

    manager.remove_characters_by_type(CharacterType.ENEMY)

    assert manager.engine.characters == []
    assert manager.turn_index == -1


# --- remove_character edge cases ---

def test_remove_last_character_resets_turn_index(manager):
    """Tests that removing the only character sets turn_index to -1."""
    manager.engine.characters = [Character("Only", 10, 0, 0, 0)]
    manager.turn_index = 0

    manager.remove_character(0)

    assert manager.engine.characters == []
    assert manager.turn_index == -1


# --- insert_character edge cases ---

def test_insert_character_when_no_initiative_rolled(manager):
    """When turn_index==-1 (no initiative), character is simply appended."""
    manager.turn_index = -1
    manager.engine.characters = [Character("A", 10, 0, 0, init=20)]

    manager.insert_character(Character("B", 10, 0, 0, init=5))

    assert manager.engine.characters[-1].name == "B"
    manager.engine.log.assert_called()

def test_insert_character_increments_turn_index_when_inserted_before_current(manager):
    """When a character is inserted at a position <= turn_index, turn_index is bumped."""
    manager.engine.characters = [
        Character("A", 10, 0, 0, init=20),
        Character("C", 10, 0, 0, init=5),
    ]
    manager.turn_index = 1  # Currently C's turn

    # B has init=15, which slots between A(20) and C(5) — index 1 <= turn_index 1
    manager.insert_character(Character("B", 10, 0, 0, init=15), surprise=False)

    assert [c.name for c in manager.engine.characters] == ["A", "B", "C"]
    assert manager.turn_index == 2   # bumped because insertion was at index <= old turn_index
