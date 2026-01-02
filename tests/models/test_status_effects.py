import pytest
import sys
import os

# sys.path.append removed. Run tests with python -m pytest

from src.models.character import Character
from src.models.status_effects import StatusEffect
from src.models.enums import StatusEffectType

@pytest.fixture
def char():
    return Character("TestChar", lp=50, rp=0, sp=0, init=10)

def test_burn_effect(char):
    """Test: Verbrennung verursacht Schaden."""
    char.add_status(StatusEffectType.BURN, duration=2, rank=3)
    log = char.update_status()

    # Rang 3 Verbrennung = 3 Schaden (Normal)
    assert char.lp == 47
    assert "Verbrennung Rang 3" in log
    assert len(char.status) == 1

def test_freeze_effect(char):
    """Test: Unterkühlung erzeugt Log-Eintrag."""
    char.add_status(StatusEffectType.FREEZE, duration=1, rank=2)
    log = char.update_status()

    assert "Unterkühlung Rang 2" in log
    assert "verliert Bonusaktion" in log

def test_exhaustion_effect(char):
    """Test: Erschöpfung erzeugt Log-Eintrag."""
    char.add_status(StatusEffectType.EXHAUSTION, duration=1, rank=1)
    log = char.update_status()

    assert "Erschöpfung" in log
    assert "-2 Malus auf GEWANDTHEIT" in log

def test_confusion_effect(char):
    """Test: Verwirrung erzeugt Log-Eintrag."""
    char.add_status(StatusEffectType.CONFUSION, duration=1, rank=1)
    log = char.update_status()

    assert "Verwirrung" in log
    assert "-1 Malus auf KAMPF-Probe" in log

def test_blind_effect(char):
    """Test: Blendung erzeugt korrekte Log-Einträge je nach Rang."""

    # Rang 1
    char.add_status(StatusEffectType.BLIND, duration=1, rank=1)
    log = char.update_status()
    assert "geblendet: -1 auf Angriffsprobe" in log
    char.status.clear() # Reset

    # Rang 3
    char.add_status(StatusEffectType.BLIND, duration=1, rank=3)
    log = char.update_status()
    assert "geblendet: -2 auf alle Aktionen" in log
    char.status.clear()

    # Rang 5
    char.add_status(StatusEffectType.BLIND, duration=1, rank=5)
    log = char.update_status()
    assert "geblendet: -3 auf alle Aktionen" in log

def test_add_status(char):
    """Test: Status wird hinzugefügt."""
    char.add_status("Vergiftung", duration=3, rank=2)
    assert len(char.status) == 1
    assert char.status[0].name == "Vergiftung"
    assert char.status[0].duration == 3
    assert char.status[0].rank == 2

def test_poison_effect(char):
    """Test: Vergiftung verursacht Direktschaden."""
    char.add_status("Vergiftung", duration=1, rank=5)
    log = char.update_status()
    # Rang 5 Vergiftung = 5 Direktschaden
    assert char.lp == 45
    assert "Vergiftung Rang 5" in log
    # Status sollte nun weg sein (Duration 1 -> 0)
    assert len(char.status) == 0

def test_bleeding_effect(char):
    """Test: Blutungsschaden steigt pro Runde."""
    # Rang 2 Blutung.
    # Runde 1 Schaden: Rang/2 + 0 = 1
    # Runde 2 Schaden: Rang/2 + 1 = 2
    char.add_status("Blutung", duration=2, rank=2)

    # Runde 1
    char.update_status()
    assert char.lp == 49 # -1

    # Runde 2
    char.update_status()
    assert char.lp == 47 # -2

def test_stun_effect(char):
    """Test: Betäubung setzt skip_turns."""
    char.add_status("Betäubung", duration=1, rank=1)
    char.update_status()
    assert char.skip_turns == 1

    # Nächste Runde (Status weg)
    char.update_status()
    assert char.skip_turns == 0

def test_erosion_effect(char):
    """Test: Erosion reduziert Max LP."""
    max_lp_start = char.max_lp
    char.add_status("Erosion", duration=1, rank=1)
    char.update_status()

    assert char.max_lp < max_lp_start
    # Erosion verursacht auch Direktschaden in Höhe des MaxLP Verlusts
    assert char.lp < 50
