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


# --- calculate_damage edge-case tests ---

@patch('src.core.mechanics.get_rules', return_value={})
def test_damage_shield_absorbs_all(mock_get_rules, char):
    """When damage <= SP the shield absorbs everything: armor and LP are untouched."""
    # char: sp=20, rp=10, lp=100
    result = calculate_damage(char, 15, DamageType.NORMAL)
    assert char.sp == 5                    # 20 - 15
    assert char.rp == 10                   # RP untouched
    assert char.lp == 100                  # LP untouched
    assert result.absorbed_by_shield == 15
    assert result.absorbed_by_armor == 0
    assert result.final_damage_hp == 0
    assert result.is_dead is False


@patch('src.core.mechanics.get_rules', return_value={})
def test_damage_armor_absorbs_all(mock_get_rules):
    """When there is no SP and damage <= rp*2 the armor absorbs everything: LP is untouched."""
    char = Character(name="Tank", lp=100, rp=10, sp=0, init=0)
    # rp=10 → can absorb up to 20 damage
    result = calculate_damage(char, 18, DamageType.NORMAL)
    assert char.lp == 100                  # LP untouched
    assert result.absorbed_by_armor == 18
    assert result.final_damage_hp == 0
    assert result.is_dead is False


@patch('src.core.mechanics.get_rules', return_value={})
def test_armor_rp_loss_formula(mock_get_rules):
    """Armor loses ceil(absorbed/2) durability: every 2 absorbed damage costs 1 RP."""
    # absorb=1 → rp_loss=(1+1)//2=1
    char1 = Character(name="C1", lp=100, rp=10, sp=0, init=0)
    r1 = calculate_damage(char1, 1, DamageType.NORMAL)
    assert r1.armor_loss == 1

    # absorb=2 → rp_loss=(2+1)//2=1
    char2 = Character(name="C2", lp=100, rp=10, sp=0, init=0)
    r2 = calculate_damage(char2, 2, DamageType.NORMAL)
    assert r2.armor_loss == 1

    # absorb=3 → rp_loss=(3+1)//2=2
    char3 = Character(name="C3", lp=100, rp=10, sp=0, init=0)
    r3 = calculate_damage(char3, 3, DamageType.NORMAL)
    assert r3.armor_loss == 2

    # absorb=4 → rp_loss=(4+1)//2=2
    char4 = Character(name="C4", lp=100, rp=10, sp=0, init=0)
    r4 = calculate_damage(char4, 4, DamageType.NORMAL)
    assert r4.armor_loss == 2


@patch('src.core.mechanics.get_rules', return_value={})
def test_damage_zero_no_state_change(mock_get_rules, char):
    """Zero damage must not alter any character attribute."""
    sp_before, rp_before, lp_before = char.sp, char.rp, char.lp
    result = calculate_damage(char, 0, DamageType.NORMAL)
    assert char.sp == sp_before
    assert char.rp == rp_before
    assert char.lp == lp_before
    assert result.final_damage_hp == 0
    assert result.is_dead is False


# --- DIRECT and PIERCING damage type tests ---

@patch('src.core.mechanics.get_rules')
def test_direct_damage_bypasses_sp_and_rp(mock_get_rules, char):
    """DIRECT damage ignores both shield and armor — goes straight to LP."""
    mock_get_rules.return_value = {
        "damage_types": {
            "DIRECT": {"ignores_shield": True, "ignores_armor": True}
        }
    }
    sp_before = char.sp   # 20
    rp_before = char.rp   # 10
    result = calculate_damage(char, 15, DamageType.DIRECT)
    assert char.sp == sp_before           # SP untouched
    assert char.rp == rp_before           # RP untouched
    assert char.lp == 85                  # 100 - 15
    assert result.absorbed_by_shield == 0
    assert result.absorbed_by_armor == 0
    assert result.final_damage_hp == 15


@patch('src.core.mechanics.get_rules', return_value={})
def test_death_check_lp_zero(mock_get_rules):
    """Character is marked dead when lp reaches 0."""
    char = Character(name="Dying", lp=5, rp=0, sp=0, init=0)
    result = calculate_damage(char, 5, DamageType.DIRECT)
    assert result.is_dead is True


@patch('src.core.mechanics.get_rules', return_value={})
def test_death_check_max_lp_zero_does_not_kill(mock_get_rules):
    """max_lp reaching 0 (e.g. via Erosion) must NOT mark a living character as dead."""
    char = Character(name="Eroded", lp=10, rp=0, sp=0, init=0)
    char.max_lp = 0  # Erosion drained all max HP
    result = calculate_damage(char, 0, DamageType.DIRECT)  # 0 dmg → lp stays 10
    assert result.is_dead is False


@patch('src.core.mechanics.get_rules')
def test_piercing_damage_sp_absorbs_rp_bypassed(mock_get_rules, char):
    """PIERCING damage: SP absorbs normally, RP (armor) is bypassed."""
    mock_get_rules.return_value = {
        "damage_types": {
            "PIERCING": {"ignores_shield": False, "ignores_armor": True}
        }
    }
    # char: sp=20, rp=10, lp=100
    rp_before = char.rp   # 10
    result = calculate_damage(char, 30, DamageType.PIERCING)
    assert char.sp == 0                   # SP exhausted (absorbed 20)
    assert char.rp == rp_before           # RP untouched
    assert char.lp == 90                  # 100 - (30 - 20) = 90
    assert result.absorbed_by_shield == 20
    assert result.absorbed_by_armor == 0
    assert result.final_damage_hp == 10
