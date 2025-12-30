import pytest
import sys
import os

# Füge das src Verzeichnis zum Pfad hinzu, damit Module importiert werden können
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.character import Character

@pytest.fixture
def char_damage():
    """Fixture für Schadens-Tests: Ein Standard-Charakter."""
    return Character("TestDummy", lp=20, rp=5, sp=10, init=10)

def test_normal_damage_full_absorb_by_shield(char_damage):
    """Test: Normaler Schaden wird komplett vom Schild absorbiert."""
    log = char_damage.apply_damage(5, "Normal")
    assert char_damage.sp == 5  # 10 - 5
    assert char_damage.rp == 5  # Unverändert
    assert char_damage.lp == 20 # Unverändert
    assert "vom Schild absorbiert" in log

def test_normal_damage_pierces_shield_absorb_by_armor(char_damage):
    """Test: Schaden bricht Schild und wird von Rüstung gefangen."""
    # 15 Schaden: 10 Schild weg, 5 Rest. Rüstung 5 absorbiert bis zu 10.
    log = char_damage.apply_damage(15, "Normal")
    assert char_damage.sp == 0
    # Restschaden 5. Rüstung absorbiert 5.
    # RP Verlust = (5 + 1) // 2 = 3.
    assert char_damage.rp == 2 # 5 - 3
    assert char_damage.lp == 20

def test_normal_damage_pierces_all(char_damage):
    """Test: Schaden bricht Schild und Rüstung und trifft LP."""
    # 25 Schaden.
    # 10 Schild -> 15 Rest.
    # Rüstung 5 absorbiert max 10.
    # 15 Rest > 10 Max Absorb -> 5 Schaden gehen durch auf LP.
    # RP Verlust für 10 Absorb = 5.
    log = char_damage.apply_damage(25, "Normal")
    assert char_damage.sp == 0
    assert char_damage.rp == 0
    assert char_damage.lp == 15 # 20 - 5

def test_piercing_damage(char_damage):
    """Test: Durchschlagender Schaden ignoriert Rüstung."""
    # 15 Schaden Durchschlagend.
    # 10 Schild -> 5 Rest.
    # Rüstung wird ignoriert.
    # 5 Schaden auf LP.
    log = char_damage.apply_damage(15, "Durchschlagend")
    assert char_damage.sp == 0
    assert char_damage.rp == 5 # Rüstung unberührt
    assert char_damage.lp == 15 # 20 - 5

def test_direct_damage(char_damage):
    """Test: Direktschaden ignoriert Schild und Rüstung."""
    log = char_damage.apply_damage(10, "Direkt")
    assert char_damage.sp == 10 # Unberührt
    assert char_damage.rp == 5  # Unberührt
    assert char_damage.lp == 10 # 20 - 10

def test_death(char_damage):
    """Test: Charakter stirbt bei LP <= 0."""
    log = char_damage.apply_damage(100, "Direkt")
    assert char_damage.lp <= 0
    assert "ist kampfunfähig" in log

@pytest.fixture
def char_status():
    """Fixture für Status-Tests."""
    return Character("StatusDummy", lp=50, rp=0, sp=0, init=10)

def test_add_status(char_status):
    """Test: Status wird hinzugefügt."""
    char_status.add_status("Vergiftung", duration=3, rank=2)
    assert len(char_status.status) == 1
    assert char_status.status[0]["effect"] == "Vergiftung"
    assert char_status.status[0]["rounds"] == 3
    assert char_status.status[0]["rank"] == 2

def test_poison_effect(char_status):
    """Test: Vergiftung verursacht Direktschaden."""
    char_status.add_status("Vergiftung", duration=1, rank=5)
    log = char_status.update_status()
    # Rang 5 Vergiftung = 5 Direktschaden
    assert char_status.lp == 45
    assert "Vergiftung Rang 5" in log
    # Status sollte nun weg sein (Duration 1 -> 0)
    assert len(char_status.status) == 0

def test_bleeding_effect(char_status):
    """Test: Blutungsschaden steigt pro Runde."""
    # Rang 2 Blutung.
    # Runde 1 Schaden: Rang/2 + 0 = 1
    # Runde 2 Schaden: Rang/2 + 1 = 2
    char_status.add_status("Blutung", duration=2, rank=2)

    # Runde 1
    char_status.update_status()
    assert char_status.lp == 49 # -1

    # Runde 2
    char_status.update_status()
    assert char_status.lp == 47 # -2

def test_stun_effect(char_status):
    """Test: Betäubung setzt skip_turns."""
    char_status.add_status("Betäubung", duration=1, rank=1)
    char_status.update_status()
    assert char_status.skip_turns == 1

    # Nächste Runde (Status weg)
    char_status.update_status()
    assert char_status.skip_turns == 0

def test_erosion_effect(char_status):
    """Test: Erosion reduziert Max LP."""
    max_lp_start = char_status.max_lp
    char_status.add_status("Erosion", duration=1, rank=1)
    char_status.update_status()

    assert char_status.max_lp < max_lp_start
    # Erosion verursacht auch Direktschaden in Höhe des MaxLP Verlusts
    assert char_status.lp < 50

def test_healing(char_status):
    """Test: Heilung erhöht LP."""
    char_status.lp = 10
    log = char_status.heal(5)
    assert char_status.lp == 15
    assert "wird um 5 LP geheilt" in log

