import pytest
from unittest.mock import patch
from src.core.mechanics import (
    wuerfle_initiative, 
    get_wuerfel_from_gewandtheit, 
    roll_exploding_dice,
    calculate_damage,
    format_damage_log
)
from src.models.character import Character
from src.models.enums import DamageType, RuleKey
from src.models.combat_results import DamageResult

# --- Fixtures ---
@pytest.fixture
def char():
    """Provides a standard character for damage calculation tests."""
    # Character constructor does not accept max_lp. It sets max_lp = lp initially.
    c = Character(name="Test Dummy", lp=100, rp=10, sp=20, init=0)
    # If we really need max_lp to be different or explicitly set (though init sets it to lp)
    # c.max_lp = 100 
    return c

@pytest.fixture
def result():
    """Provides a basic DamageResult instance."""
    return DamageResult(original_damage=10, damage_type="Normal", rank=1)

# --- Dice Rolling Tests ---

def test_gewandtheit_mapping():
    assert get_wuerfel_from_gewandtheit(1) == 4
    assert get_wuerfel_from_gewandtheit(6) == 20

def test_exploding_dice_logic():
    with patch('random.randint', side_effect=[6, 2]):
        total, _ = roll_exploding_dice(6)
        assert total == 8

# --- calculate_damage Tests ---

@patch('src.core.mechanics.get_rules', return_value={})
def test_damage_full_flow(mock_get_rules, char):
    """Tests a large hit that goes through shield, armor, and HP."""
    result = calculate_damage(char, 50, DamageType.NORMAL)
    assert char.sp == 0
    assert char.rp == 0
    assert char.lp == 90
    assert result.absorbed_by_shield == 20
    assert result.absorbed_by_armor == 20
    assert result.armor_loss == 10
    assert result.final_damage_hp == 10

@patch('src.core.mechanics.get_rules')
def test_damage_ignores_armor(mock_get_rules, char):
    """Tests damage with the 'ignores_armor' rule."""
    mock_get_rules.return_value = {RuleKey.DAMAGE_TYPES.value: {"Piercing": {RuleKey.IGNORES_ARMOR.value: True}}}
    result = calculate_damage(char, 30, "Piercing")
    assert char.rp == 10 # Armor is untouched
    assert result.absorbed_by_armor == 0

# --- format_damage_log Tests ---

@patch('src.core.mechanics.get_rules', return_value={})
def test_format_log_simple_damage(mock_get_rules, char):
    """Tests the log for simple HP damage — character name and amount must appear."""
    result = calculate_damage(char, 5, DamageType.DIRECT)  # Direct goes straight to LP
    log = format_damage_log(char, result)
    assert "Test Dummy" in log
    assert "5" in log

@patch('src.core.mechanics.get_rules', return_value={})
def test_format_log_shield_absorption(mock_get_rules, char):
    """Tests that shield absorption is mentioned in the log."""
    result = calculate_damage(char, 10, DamageType.NORMAL)
    log = format_damage_log(char, result)
    assert "shield" in log.lower()
    assert "10" in log

@patch('src.core.mechanics.get_rules', return_value={})
def test_format_log_armor_absorption(mock_get_rules):
    """Tests that armor absorption and RP loss are mentioned in the log."""
    char = Character(name="Tank", lp=100, rp=10, sp=0, init=0)
    result = calculate_damage(char, 15, DamageType.NORMAL)
    log = format_damage_log(char, result)
    assert "armor" in log.lower()
    assert "RP" in log

@patch('src.core.mechanics.get_rules', return_value={})
def test_format_log_is_dead(mock_get_rules):
    """Tests that a defeated character is noted in the log."""
    char = Character(name="Victim", lp=5, rp=0, sp=0, init=0)
    result = calculate_damage(char, 10, DamageType.DIRECT)
    log = format_damage_log(char, result)
    assert "Victim" in log
    assert "down" in log.lower()

def test_format_log_secondary_effect(char, result):
    """Tests that a secondary effect chance appears in the log."""
    result.secondary_effect = "Burn"
    result.rank = 2
    log = format_damage_log(char, result)
    assert "Burn" in log
    assert "2" in log

def test_format_log_ignores_armor(char, result):
    """Tests that armor-ignoring damage is noted in the log."""
    result.ignores_armor = True
    log = format_damage_log(char, result)
    assert "armor" in log.lower()

def test_format_log_with_details(char, result):
    """Tests that has_details=True uses the generic damage header (no type name)."""
    log = format_damage_log(char, result, has_details=True)
    # With has_details the first line uses receives_damage (no type), not receives_typed_damage
    assert "Test Dummy" in log
    assert "10" in log


# --- GEW boundary and exploding dice safety break ---

def test_get_wuerfel_below_min_returns_d4():
    """GEW < 1 clamps to d4."""
    assert get_wuerfel_from_gewandtheit(0) == 4
    assert get_wuerfel_from_gewandtheit(-5) == 4

def test_get_wuerfel_above_max_returns_d20():
    """GEW > 6 clamps to d20."""
    assert get_wuerfel_from_gewandtheit(7) == 20
    assert get_wuerfel_from_gewandtheit(100) == 20

def test_roll_exploding_dice_safety_break():
    """After 20 consecutive max-face rolls the loop breaks to prevent infinite recursion."""
    # Always return max face (sides=6) so the loop would be infinite without the safety break
    with patch('random.randint', return_value=6):
        total, rolls = roll_exploding_dice(6)
    assert len(rolls) == 21   # 1 initial + 20 safety-break limit
    assert total == 21 * 6
