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

@patch('src.models.character.get_rules')
def test_add_status_non_stackable_replaces_existing(mock_get_rules, char):
    """Non-stackable effect added twice → only one instance, duration refreshed."""
    mock_get_rules.return_value = {"status_effects": {"STUN": {"max_rank": 1, "stackable": False}}}
    char.add_status("STUN", 3, 1)
    assert len(char.status) == 1

    char.add_status("STUN", 5, 1)  # second application → should refresh, not stack
    assert len(char.status) == 1
    assert char.status[0].duration == 5  # duration updated to new value


@patch('src.models.character.get_rules')
def test_add_status_stackable_creates_second_instance(mock_get_rules, char):
    """Stackable effect added twice → two separate instances."""
    mock_get_rules.return_value = {"status_effects": {"POISON": {"max_rank": 5, "stackable": True}}}
    char.add_status("POISON", 3, 1)
    char.add_status("POISON", 3, 2)
    assert len(char.status) == 2


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

# --- heal() edge cases ---

def test_heal_capped_at_max_lp(char):
    """Tests that healing is capped at max_lp by default."""
    char.lp = 90
    char.max_lp = 100
    char.heal(50)  # Would go to 140
    assert char.lp == 100

def test_heal_at_full_hp_no_change(char):
    """Tests that healing a full-HP character leaves LP unchanged."""
    char.lp = 100
    char.max_lp = 100
    char.heal(20)
    assert char.lp == 100

def test_heal_with_overheal_exceeds_max(char):
    """Tests that allow_overheal=True lets LP exceed max_lp."""
    char.lp = 90
    char.max_lp = 100
    char.heal(30, allow_overheal=True)
    assert char.lp == 120

def test_heal_returns_message_string(char):
    """Tests that heal() returns a non-empty log string."""
    char.lp = 80
    result = char.heal(10)
    assert isinstance(result, str)
    assert len(result) > 0


# --- Status effect stacking ---

@patch('src.models.character.get_rules', return_value={})
def test_add_same_status_twice_extends_duration(mock_get_rules, char):
    """Tests that adding the same status effect twice accumulates entries."""
    char.add_status("CustomFx", 3, 1)
    char.add_status("CustomFx", 3, 1)
    # Current implementation appends; both entries should be present
    assert len(char.status) == 2

# --- apply_damage() direct call Tests ---

@patch('src.models.character.calculate_damage')
def test_apply_damage_reduces_lp(mock_calc, char):
    """Direct Character.apply_damage() call delegates to calculate_damage and returns its result."""
    from src.models.combat_results import DamageResult
    expected = DamageResult(original_damage=10, damage_type="NORMAL", rank=1, final_damage_hp=10)
    mock_calc.return_value = expected

    result = char.apply_damage(10, "NORMAL", 1)

    mock_calc.assert_called_once_with(char, 10, "NORMAL", 1)
    assert result is expected


@patch('src.core.mechanics.get_rules')
def test_apply_damage_direct_type_bypasses_shield_and_armor(mock_rules):
    """Character.apply_damage() with DamageType.DIRECT, backed by rules that mark it as
    ignores_shield + ignores_armor: SP and RP must remain untouched and all damage hits LP."""
    from src.models.enums import DamageType
    mock_rules.return_value = {
        "damage_types": {
            "DIRECT": {"ignores_shield": True, "ignores_armor": True}
        }
    }
    c = Character(name="Tank", lp=50, rp=10, sp=10, init=0)
    sp_before, rp_before = c.sp, c.rp
    c.apply_damage(15, DamageType.DIRECT, 1)
    assert c.sp == sp_before   # SP untouched
    assert c.rp == rp_before   # RP untouched
    assert c.lp == 35          # 50 - 15


@patch('src.core.mechanics.get_rules', return_value={})
def test_apply_damage_lp_reduced_by_exact_amount_with_no_sp_rp(mock_rules):
    """With SP=0 and RP=0 all damage reaches LP directly."""
    c = Character(name="Fragile", lp=30, rp=0, sp=0, init=0)
    c.apply_damage(12, "NORMAL", 1)
    assert c.lp == 18


@patch('src.core.mechanics.get_rules', return_value={})
def test_apply_damage_returns_damage_result_instance(mock_rules):
    """apply_damage() must return a DamageResult object."""
    from src.models.combat_results import DamageResult
    c = Character(name="Hero", lp=100, rp=0, sp=0, init=0)
    result = c.apply_damage(5, "NORMAL", 1)
    assert isinstance(result, DamageResult)


@patch('src.core.mechanics.get_rules', return_value={})
def test_apply_damage_marks_dead_when_lp_reaches_zero(mock_rules):
    """apply_damage() result.is_dead is True when LP drops to 0."""
    c = Character(name="Dying", lp=5, rp=0, sp=0, init=0)
    result = c.apply_damage(5, "NORMAL", 1)
    assert result.is_dead is True
    assert c.lp <= 0


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
