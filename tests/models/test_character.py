import pytest
import sys
import os

# sys.path.append removed. Run tests with python -m pytest

from src.models.character import Character
from src.models.enums import DamageType, StatusEffectType
from src.models.combat_results import DamageResult

@pytest.fixture
def char_damage():
    """Fixture für Schadens-Tests: Ein Standard-Charakter."""
    return Character("TestDummy", lp=20, rp=5, sp=10, init=10)

def test_normal_damage_full_absorb_by_shield(char_damage):
    """Test: Normaler Schaden wird komplett vom Schild absorbiert."""
    result = char_damage.apply_damage(5, "Normal")
    assert char_damage.sp == 5  # 10 - 5
    assert char_damage.rp == 5  # Unverändert
    assert char_damage.lp == 20 # Unverändert
    assert result.absorbed_by_shield == 5
    assert result.final_damage_hp == 0

def test_normal_damage_pierces_shield_absorb_by_armor(char_damage):
    """Test: Schaden bricht Schild und wird von Rüstung gefangen."""
    # 15 Schaden: 10 Schild weg, 5 Rest. Rüstung 5 absorbiert bis zu 10.
    result = char_damage.apply_damage(15, "Normal")
    assert char_damage.sp == 0
    # Restschaden 5. Rüstung absorbiert 5.
    # RP Verlust = (5 + 1) // 2 = 3.
    assert char_damage.rp == 2 # 5 - 3
    assert char_damage.lp == 20
    assert result.absorbed_by_shield == 10
    assert result.absorbed_by_armor == 5
    assert result.final_damage_hp == 0

def test_normal_damage_pierces_all(char_damage):
    """Test: Schaden bricht Schild und Rüstung und trifft LP."""
    # 25 Schaden.
    # 10 Schild -> 15 Rest.
    # Rüstung 5 absorbiert max 10.
    # 15 Rest > 10 Max Absorb -> 5 Schaden gehen durch auf LP.
    # RP Verlust für 10 Absorb = 5.
    result = char_damage.apply_damage(25, "Normal")
    assert char_damage.sp == 0
    assert char_damage.rp == 0
    assert char_damage.lp == 15 # 20 - 5
    assert result.absorbed_by_shield == 10
    assert result.absorbed_by_armor == 10
    assert result.final_damage_hp == 5

def test_piercing_damage(char_damage):
    """Test: Durchschlagender Schaden ignoriert Rüstung."""
    # 15 Schaden Durchschlagend.
    # 10 Schild -> 5 Rest.
    # Rüstung wird ignoriert.
    # 5 Schaden auf LP.
    result = char_damage.apply_damage(15, "Durchschlagend")
    assert char_damage.sp == 0
    assert char_damage.rp == 5 # Rüstung unberührt
    assert char_damage.lp == 15 # 20 - 5
    assert result.ignores_armor is True
    assert result.absorbed_by_shield == 10
    assert result.final_damage_hp == 5

def test_direct_damage(char_damage):
    """Test: Direktschaden ignoriert Schild und Rüstung."""
    result = char_damage.apply_damage(10, "Direkt")
    assert char_damage.sp == 10 # Unberührt
    assert char_damage.rp == 5  # Unberührt
    assert char_damage.lp == 10 # 20 - 10
    assert result.ignores_armor is True
    assert result.ignores_shield is True
    assert result.final_damage_hp == 10

def test_death(char_damage):
    """Test: Charakter stirbt bei LP <= 0."""
    result = char_damage.apply_damage(100, "Direkt")
    assert char_damage.lp <= 0
    assert result.is_dead is True

def test_healing(char_damage):
    """Test: Heilung erhöht LP."""
    char_damage.lp = 10
    log = char_damage.heal(5)
    assert char_damage.lp == 15
    assert "wird um 5 LP geheilt" in log

def test_elemental_damage_logging(char_damage):
    """Test: Elementarschaden wird korrekt geloggt und zeigt Chance auf Sekundäreffekt."""
    # Teste Feuer (sollte Chance auf Verbrennung anzeigen)
    result = char_damage.apply_damage(5, DamageType.FIRE)
    assert result.damage_type == DamageType.FIRE
    assert result.secondary_effect == StatusEffectType.BURN

    # Teste Gift (sollte Chance auf Vergiftung anzeigen)
    result = char_damage.apply_damage(5, DamageType.POISON)
    assert result.damage_type == DamageType.POISON
    assert result.secondary_effect == StatusEffectType.POISON

    # Teste Blitz (sollte Chance auf Betäubung anzeigen)
    result = char_damage.apply_damage(5, DamageType.LIGHTNING)
    assert result.damage_type == DamageType.LIGHTNING
    assert result.secondary_effect == StatusEffectType.STUN

    # Teste Kälte (sollte Chance auf Unterkühlung anzeigen)
    result = char_damage.apply_damage(5, DamageType.COLD)
    assert result.damage_type == DamageType.COLD
    assert result.secondary_effect == StatusEffectType.FREEZE

    # Teste Verwesung (sollte Chance auf Erosion anzeigen)
    result = char_damage.apply_damage(5, DamageType.DECAY)
    assert result.damage_type == DamageType.DECAY
    assert result.secondary_effect == StatusEffectType.EROSION
