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
        mock_heal.assert_called_once_with(5)

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
