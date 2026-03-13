import pytest
from unittest.mock import patch, MagicMock
from src.models.character import Character
from src.models.status_effects import (
    StatusEffect,
    PoisonEffect,
    BurnEffect,
    BleedEffect,
    ErosionEffect,
    FreezeEffect,
    StunEffect,
    ExhaustionEffect,
    ConfusionEffect,
    BlindEffect,
    DisarmedEffect,
    RegenerationEffect,
    GenericStatusEffect,
    EFFECT_CLASSES
)
from src.models.enums import StatusEffectType
from src.models.combat_results import DamageResult

@pytest.fixture
def char():
    """Provides a standard character for status effect tests."""
    # Character constructor does not accept max_lp. It sets max_lp = lp initially.
    c = Character(name="Test Dummy", lp=100, rp=10, sp=10, init=10)
    # If we really need max_lp to be different or explicitly set (though init sets it to lp)
    # c.max_lp = 100 
    return c

# --- apply_round_effect Tests for each specific effect ---

@patch('src.models.status_effects.calculate_damage')
def test_poison_effect(mock_calculate, char):
    """Tests that PoisonEffect deals direct damage equal to its rank."""
    # Mock return value to be a DamageResult, not a MagicMock that fails comparison
    mock_result = DamageResult(original_damage=2, damage_type="DIRECT", rank=2)
    mock_calculate.return_value = mock_result
    
    effect = PoisonEffect(duration=3, rank=2)
    effect.apply_round_effect(char)
    mock_calculate.assert_called_once_with(char, 2, "DIRECT")

@patch('src.models.status_effects.calculate_damage')
def test_burn_effect(mock_calculate, char):
    """Tests that BurnEffect deals normal damage equal to its rank."""
    mock_result = DamageResult(original_damage=3, damage_type="NORMAL", rank=3)
    mock_calculate.return_value = mock_result

    effect = BurnEffect(duration=3, rank=3)
    effect.apply_round_effect(char)
    mock_calculate.assert_called_once_with(char, 3, "NORMAL")

@patch('src.models.status_effects.calculate_damage')
def test_bleed_effect_damage_scaling(mock_calculate, char):
    """Tests the scaling damage formula of BleedEffect."""
    effect = BleedEffect(duration=5, rank=4)
    
    # Round 1: dmg = int(4/2) + (1-1) = 2
    mock_result1 = DamageResult(original_damage=2, damage_type="NORMAL", rank=4)
    mock_calculate.return_value = mock_result1
    
    effect.active_rounds = 1
    effect.apply_round_effect(char)
    mock_calculate.assert_called_with(char, 2, "NORMAL")
    
    # Round 3: dmg = int(4/2) + (3-1) = 4
    mock_result2 = DamageResult(original_damage=4, damage_type="NORMAL", rank=4)
    mock_calculate.return_value = mock_result2
    
    effect.active_rounds = 3
    effect.apply_round_effect(char)
    mock_calculate.assert_called_with(char, 4, "NORMAL")

@patch('random.randint', return_value=3)
def test_erosion_effect(mock_randint, char):
    """ErosionEffect reduces max_lp permanently and clamps current LP to the new max.
    It does NOT deal separate direct damage (no double-hit)."""
    lp_before = char.lp  # 100
    effect = ErosionEffect(duration=2, rank=2)
    # dmg = rank(2) * randint(3) = 6
    effect.apply_round_effect(char)

    assert char.max_lp == 94           # max_lp reduced
    assert char.lp == 94               # current LP clamped to new max (was 100 > 94)
    assert char.lp == char.max_lp      # invariant: lp never exceeds max_lp

def test_stun_effect(char):
    """Tests that StunEffect sets skip_turns on the character."""
    effect = StunEffect(duration=1, rank=1)
    effect.apply_round_effect(char)
    assert char.skip_turns == 1

# --- Serialization (to_dict / from_dict) Tests ---

def test_to_dict_and_from_dict_specific_class():
    """Tests that a specific effect is correctly serialized and deserialized."""
    original_effect = PoisonEffect(duration=3, rank=2)
    original_effect.active_rounds = 1
    
    effect_dict = original_effect.to_dict()
    
    assert effect_dict['effect'] == StatusEffectType.POISON.value
    assert effect_dict['rounds'] == 3
    assert effect_dict['rank'] == 2
    assert effect_dict['active_rounds'] == 1
    
    rehydrated_effect = StatusEffect.from_dict(effect_dict)
    
    assert isinstance(rehydrated_effect, PoisonEffect)
    assert rehydrated_effect.duration == 3
    assert rehydrated_effect.rank == 2
    assert rehydrated_effect.active_rounds == 1

def test_from_dict_generic_fallback():
    """Tests that an unknown effect name falls back to GenericStatusEffect."""
    unknown_effect_dict = {
        "effect": "MadeUpEffect",
        "rounds": 5,
        "rank": 1
    }
    
    rehydrated_effect = StatusEffect.from_dict(unknown_effect_dict)
    
    assert isinstance(rehydrated_effect, GenericStatusEffect)
    assert rehydrated_effect.name == "MadeUpEffect"

def test_from_dict_all_known_effects():
    """Tests that all known effects in EFFECT_CLASSES are correctly deserialized."""
    for name, effect_class in EFFECT_CLASSES.items():
        data = {"effect": name, "rounds": 1, "rank": 1}
        effect = StatusEffect.from_dict(data)
        assert isinstance(effect, effect_class), f"Failed for effect: {name}"


# --- Missing effect apply_round_effect Tests ---

def test_freeze_effect_returns_message(char):
    """Tests that FreezeEffect returns a non-empty message string."""
    effect = FreezeEffect(duration=2, rank=3)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0

def test_freeze_effect_does_not_modify_char(char):
    """Tests that FreezeEffect does not change character HP/SP/RP."""
    effect = FreezeEffect(duration=2, rank=1)
    lp_before, rp_before, sp_before = char.lp, char.rp, char.sp
    effect.apply_round_effect(char)
    assert char.lp == lp_before
    assert char.rp == rp_before
    assert char.sp == sp_before

def test_exhaustion_effect_returns_message(char):
    """Tests that ExhaustionEffect returns a non-empty message string."""
    effect = ExhaustionEffect(duration=1, rank=1)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0

def test_confusion_effect_returns_message(char):
    """Tests that ConfusionEffect returns a non-empty message string."""
    effect = ConfusionEffect(duration=1, rank=1)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.parametrize("rank", [1, 2, 3, 4, 5, 6])
def test_blind_effect_all_ranks(char, rank):
    """Tests that BlindEffect returns a non-empty message for every rank."""
    effect = BlindEffect(duration=2, rank=rank)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0

def test_blind_effect_does_not_modify_char(char):
    """Tests that BlindEffect does not change character stats."""
    effect = BlindEffect(duration=1, rank=2)
    lp_before, sp_before, rp_before = char.lp, char.sp, char.rp
    effect.apply_round_effect(char)
    assert char.lp == lp_before
    assert char.sp == sp_before
    assert char.rp == rp_before

def test_disarmed_effect_returns_message(char):
    """Tests that DisarmedEffect returns a non-empty message string."""
    effect = DisarmedEffect(duration=1, rank=1)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0

def test_regeneration_effect_heals_character(char):
    """Tests that RegenerationEffect heals the character by its rank."""
    char.lp = 80  # Below max_lp of 100
    effect = RegenerationEffect(duration=3, rank=5)
    effect.apply_round_effect(char)
    assert char.lp == 85  # Healed by rank=5

def test_regeneration_effect_capped_at_max_lp(char):
    """Tests that RegenerationEffect does not exceed max_lp by default."""
    char.lp = 98
    char.max_lp = 100
    effect = RegenerationEffect(duration=1, rank=10)
    effect.apply_round_effect(char)
    assert char.lp == 100  # Capped at max_lp

def test_regeneration_effect_returns_message(char):
    """Tests that RegenerationEffect returns a message string."""
    char.lp = 50
    effect = RegenerationEffect(duration=1, rank=2)
    result = effect.apply_round_effect(char)
    assert isinstance(result, str)
    assert len(result) > 0


# --- Edge case / floor tests ---

@patch('src.models.status_effects.calculate_damage')
def test_bleed_effect_minimum_floor(mock_calculate, char):
    """rank=1, active_rounds=1: int(1/2 + 0) = int(0.5) = 0, clamped to minimum 1."""
    mock_result = DamageResult(original_damage=1, damage_type="NORMAL", rank=1)
    mock_calculate.return_value = mock_result

    effect = BleedEffect(duration=3, rank=1)
    effect.active_rounds = 1
    effect.apply_round_effect(char)

    # Must be called with 1, not 0
    mock_calculate.assert_called_with(char, 1, "NORMAL")


@patch('random.randint', return_value=4)
def test_erosion_effect_max_lp_floor_at_zero(mock_randint, char):
    """ErosionEffect floors max_lp at 0 and clamps current LP accordingly."""
    # dmg = rank(2) * randint(4) = 8; max_lp=3 → would go to -5 without floor
    char.max_lp = 3
    char.lp = 3
    effect = ErosionEffect(duration=1, rank=2)
    effect.apply_round_effect(char)

    assert char.max_lp == 0   # floored at 0
    assert char.lp == 0       # clamped to new max_lp
