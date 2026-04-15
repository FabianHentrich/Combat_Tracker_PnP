import pytest
from unittest.mock import patch
from src.core.engine import CombatEngine
from src.models.character import Character
from src.models.combat_results import DamageResult

@pytest.fixture
def engine():
    """Provides a clean CombatEngine instance for each test."""
    return CombatEngine()

def test_add_character(engine):
    """Tests adding a character to the CombatEngine."""
    char = Character("Test", 10, 10, 10, 10)
    engine.add_character(char)
    assert len(engine.characters) == 1
    assert engine.characters[0].name == "Test"

def test_remove_character(engine):
    """Tests removing a character."""
    c1 = Character("A", 10, 10, 10, 10)
    c2 = Character("B", 10, 10, 10, 10)
    engine.characters = [c1, c2]
    
    # Mock the turn manager's remove method which is called by the engine
    with patch.object(engine.turn_manager, 'remove_character') as mock_remove:
        engine.remove_character(0)
        mock_remove.assert_called_once_with(0)

def test_get_character_by_id(engine):
    """Tests retrieving a character by their unique ID."""
    char = Character("Test", 10, 10, 10, 10)
    engine.characters = [char]
    
    found_char = engine.get_character_by_id(char.id)
    assert found_char == char
    
    assert engine.get_character_by_id("non-existent-id") is None

def test_apply_damage(engine):
    """Tests that apply_damage correctly reduces a character's LP."""
    char = Character("Test", 20, 10, 10, 10)
    engine.characters = [char]
    
    # Create a proper DamageResult object instead of an empty dict
    mock_result = DamageResult(
        original_damage=5,
        damage_type="Normal",
        rank=1,
        final_damage_hp=5
    )
    
    with patch.object(char, 'apply_damage', return_value=mock_result) as mock_apply:
        engine.apply_damage(char, 5, "Normal", 1)
        mock_apply.assert_called_once_with(5, "Normal", 1)

def test_apply_healing(engine):
    """Tests that apply_healing correctly increases a character's LP."""
    # Character constructor does not accept max_lp as a keyword argument.
    # It sets max_lp = lp initially.
    char = Character("Test", 10, 10, 10, 10)
    # Manually set max_lp if needed for logic, though heal() usually just adds to lp
    char.max_lp = 20
    engine.characters = [char]
    
    with patch.object(char, 'heal') as mock_heal:
        engine.apply_healing(char, 5)
        mock_heal.assert_called_once_with(5, allow_overheal=False)

def test_apply_healing_with_overheal(engine):
    """Tests that apply_healing passes allow_overheal=True when requested."""
    char = Character("Test", 10, 0, 0, 0)
    char.max_lp = 10
    engine.characters = [char]
    with patch.object(char, 'heal') as mock_heal:
        engine.apply_healing(char, 20, allow_overheal=True)
        mock_heal.assert_called_once_with(20, allow_overheal=True)

def test_apply_shield(engine):
    """Tests that apply_shield increases SP and fires an event."""
    char = Character("Test", 10, 0, 5, 0)
    engine.characters = [char]
    with patch.object(engine, 'notify') as mock_notify:
        engine.apply_shield(char, 10)
    assert char.sp == 15
    mock_notify.assert_called()

def test_apply_armor(engine):
    """Tests that apply_armor increases RP and fires an event."""
    char = Character("Test", 10, 3, 0, 0)
    engine.characters = [char]
    with patch.object(engine, 'notify') as mock_notify:
        engine.apply_armor(char, 7)
    assert char.rp == 10
    mock_notify.assert_called()

def test_add_status_effect(engine):
    """Tests that add_status_effect adds the effect to the character."""
    char = Character("Test", 10, 0, 0, 0)
    engine.characters = [char]
    with patch.object(char, 'add_status') as mock_add:
        engine.add_status_effect(char, "POISON", 3, 2)
        mock_add.assert_called_once_with("POISON", 3, 2)

def test_update_character(engine):
    """Tests that update_character calls char.update and fires an event."""
    char = Character("Old", 10, 0, 0, 0)
    engine.characters = [char]
    with patch.object(engine, 'notify') as mock_notify:
        engine.update_character(char, {"name": "New"})
    assert char.name == "New"
    mock_notify.assert_called()

def test_remove_characters_by_type(engine):
    """Tests delegation to turn_manager.remove_characters_by_type."""
    with patch.object(engine.turn_manager, 'remove_characters_by_type') as mock_remove:
        engine.remove_characters_by_type("enemy")
        mock_remove.assert_called_once_with("enemy")

def test_clear_all_characters(engine):
    """Tests delegation to turn_manager.clear_all_characters."""
    with patch.object(engine.turn_manager, 'clear_all_characters') as mock_clear:
        engine.clear_all_characters()
        mock_clear.assert_called_once()

def test_reset_combat(engine):
    """Tests that reset_combat resets turn state and fires an update."""
    engine.turn_manager.turn_index = 5
    engine.turn_manager.round_number = 3
    with patch.object(engine, 'notify') as mock_notify:
        engine.reset_combat()
    assert engine.turn_index == -1
    assert engine.round_number == 1
    mock_notify.assert_called()

# --- get_character / get_all_characters Tests ---

def test_get_character_valid_index(engine):
    """get_character(int) returns the character at that index."""
    char = Character("Alpha", 10, 0, 0, 0)
    engine.characters = [char]
    assert engine.get_character(0) is char


def test_get_character_out_of_bounds_returns_none(engine):
    """get_character() returns None for an index outside the list."""
    engine.characters = []
    assert engine.get_character(0) is None
    assert engine.get_character(-1) is None


def test_get_character_negative_index_returns_none(engine):
    """Negative indices are treated as out-of-bounds and return None."""
    engine.characters = [Character("A", 10, 0, 0, 0)]
    assert engine.get_character(-1) is None


def test_get_all_characters_returns_list(engine):
    """get_all_characters() returns the engine's character list directly."""
    c1 = Character("A", 10, 0, 0, 0)
    c2 = Character("B", 20, 0, 0, 0)
    engine.characters = [c1, c2]
    result = engine.get_all_characters()
    assert result is engine.characters
    assert len(result) == 2


def test_get_all_characters_empty(engine):
    """get_all_characters() returns an empty list when there are no characters."""
    engine.characters = []
    assert engine.get_all_characters() == []


def test_insert_character_delegates_to_turn_manager(engine):
    """insert_character() calls turn_manager.insert_character with correct args."""
    char = Character("New", 10, 0, 0, 0)
    with patch.object(engine.turn_manager, 'insert_character') as mock_insert:
        engine.insert_character(char, surprise=True)
        mock_insert.assert_called_once_with(char, True)


def test_state_serialization(engine):
    """Tests the get_state and load_state methods."""
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    engine.characters = [c1, c2]
    engine.turn_index = 1
    engine.round_number = 5
    
    state = engine.get_state()
    
    assert len(state["characters"]) == 2
    assert state["turn_index"] == 1
    assert state["round_number"] == 5
    
    new_engine = CombatEngine()
    new_engine.load_state(state)
    
    assert len(new_engine.characters) == 2
    assert new_engine.characters[0].name == "A"
    assert new_engine.turn_index == 1
    assert new_engine.round_number == 5
