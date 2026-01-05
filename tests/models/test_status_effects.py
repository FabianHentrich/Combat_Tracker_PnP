import pytest
from unittest.mock import patch, MagicMock
from src.models.character import Character
from src.models.status_effects import (
    StatusEffect,
    PoisonEffect,
    BurnEffect,
    BleedEffect,
    ErosionEffect,
    StunEffect,
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

@patch('src.models.status_effects.calculate_damage')
@patch('random.randint', return_value=3)
def test_erosion_effect(mock_randint, mock_calculate, char):
    """Tests that ErosionEffect reduces max_lp and deals direct damage."""
    mock_result = DamageResult(original_damage=6, damage_type="DIRECT", rank=2)
    mock_calculate.return_value = mock_result

    effect = ErosionEffect(duration=2, rank=2)
    # Damage = rank * randint(1,4) = 2 * 3 = 6
    
    effect.apply_round_effect(char)
    
    assert char.max_lp == 94 # 100 - 6
    mock_calculate.assert_called_once_with(char, 6, "DIRECT")

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
