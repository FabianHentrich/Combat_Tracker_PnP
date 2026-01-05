import pytest
from unittest.mock import patch
from src.models.character import Character
from src.models.enums import CharacterType, StatType
from src.models.status_effects import PoisonEffect, GenericStatusEffect

@pytest.fixture
def char():
    """Provides a basic character instance for tests."""
    return Character(name="Hero", lp=100, rp=10, sp=20, init=15, gew=3, char_type=CharacterType.PLAYER)

# --- Initialization and State ---

def test_character_initialization(char):
    """Tests that a character is initialized with the correct attributes."""
    assert char.name == "Hero"
    assert char.max_lp == 100
    assert char.lp == 100
    assert char.char_type == CharacterType.PLAYER
    assert char.id is not None

# --- Status Effect Management ---

@patch('src.models.character.get_rules', return_value={})
def test_add_status_generic(mock_get_rules, char):
    """Tests adding a generic status effect when no specific class is found."""
    char.add_status("CustomEffect", 3, 2)
    assert len(char.status) == 1
    effect = char.status[0]
    assert isinstance(effect, GenericStatusEffect)
    assert effect.name == "CustomEffect"
    assert effect.duration == 3
    assert effect.rank == 2

@patch('src.models.character.get_rules')
def test_add_status_with_rank_capping(mock_get_rules, char):
    """Tests that the rank of a new status effect is capped by the rules."""
    mock_get_rules.return_value = {"status_effects": {"POISON": {"max_rank": 3}}}
    
    # Add a status with a rank higher than the max
    char.add_status("POISON", 5, 5)
    
    assert len(char.status) == 1
    effect = char.status[0]
    assert isinstance(effect, PoisonEffect)
    assert effect.rank == 3 # Should be capped to 3

def test_get_status_string(char):
    """Tests the formatting of the status effect string for the UI."""
    assert char.get_status_string() == "" # Should be empty initially
    
    char.add_status("POISON", 3, 1)
    char.add_status("Custom", 2, 2)
    
    # Note: This test relies on the translation keys.
    # It's a trade-off, but it validates the core formatting logic.
    # The actual output depends on the loaded language file.
    # Since we can't easily mock the global localization_manager in a clean way without affecting other tests,
    # we should check for the structure or mock the translate function used inside Character.
    
    with patch('src.models.character.translate') as mock_translate:
        # Configure mock to return predictable strings
        def side_effect(key, **kwargs):
            if key == "status_effects.POISON": return "Poison"
            if key == "status_effects.Custom": return "status_effects.Custom" # Fallback behavior
            if key == "action_panel.rank": return "Rank"
            if key == "common.rounds": return "rds."
            if key == "character_list.status": return "Status"
            return key
            
        mock_translate.side_effect = side_effect
        
        expected_str = " | Status: Poison (Rank 1, 3 rds.), Custom (Rank 2, 2 rds.)"
        assert char.get_status_string() == expected_str

# --- Serialization (to_dict / from_dict) ---

def test_to_dict_and_from_dict_serialization(char):
    """Tests that a character can be serialized to a dict and back without data loss."""
    char.add_status("POISON", 3, 1)
    char.lp = 50 # Change current LP
    
    char_dict = char.to_dict()
    
    assert char_dict[StatType.NAME] == "Hero"
    assert char_dict[StatType.LP] == 50
    assert char_dict[StatType.MAX_LP] == 100
    assert len(char_dict[StatType.STATUS]) == 1
    assert char_dict[StatType.STATUS][0]['effect'] == "POISON"
    
    rehydrated_char = Character.from_dict(char_dict)
    
    assert rehydrated_char.id == char.id
    assert rehydrated_char.name == "Hero"
    assert rehydrated_char.lp == 50
    assert len(rehydrated_char.status) == 1
    assert isinstance(rehydrated_char.status[0], PoisonEffect)

def test_from_dict_with_missing_data():
    """Tests that a character can be created from an incomplete dictionary using defaults."""
    # Missing several fields, including rp, sp, gew, etc.
    incomplete_data = {
        StatType.ID: "test-id",
        StatType.NAME: "Incomplete",
        StatType.MAX_LP: 50,
    }
    
    char = Character.from_dict(incomplete_data)
    
    assert char.id == "test-id"
    assert char.name == "Incomplete"
    assert char.max_lp == 50
    assert char.lp == 50 # Should default to max_lp
    assert char.rp == 0 # Should use default from constructor
    assert char.gew == 1 # Should use default from constructor
    assert char.char_type == CharacterType.ENEMY # Should use default

# --- Other Methods ---

def test_update_method(char):
    """Tests the update method for modifying character attributes."""
    update_data = {
        StatType.NAME: "NewName",
        StatType.LP: 80,
        StatType.MAX_RP: 15
    }
    char.update(update_data)
    
    assert char.name == "NewName"
    assert char.lp == 80
    assert char.max_rp == 15
    assert char.rp == 10 # Should not change if not in data
