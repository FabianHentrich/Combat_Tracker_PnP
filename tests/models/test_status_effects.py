import pytest
from unittest.mock import MagicMock, patch
from src.models.character import Character
from src.core.engine import CombatEngine
from src.models.enums import StatusEffectType

@pytest.fixture
def engine_with_char():
    """Erstellt eine CombatEngine mit einem Charakter."""
    engine = CombatEngine()
    char = Character("TestChar", lp=50, rp=0, sp=0, init=10)
    engine.add_character(char)
    engine.roll_initiatives() # Startet den Kampf
    # Mock den Logger, um die Ausgabe zu erfassen
    engine.log = MagicMock()
    return engine, char

def test_burn_effect(engine_with_char):
    """Test: Verbrennung verursacht Schaden, wenn der nächste Zug beginnt."""
    engine, char = engine_with_char
    char.add_status(StatusEffectType.BURN, duration=2, rank=3)
    
    engine.next_turn() # Effekt wird angewendet

    # Rang 3 Verbrennung = 3 Schaden (Normal)
    assert char.lp == 47
    assert len(char.status) == 1 # Dauer war 2, jetzt 1
    
    # Prüfen, ob der Log die richtige Nachricht enthält
    log_calls = [call.args[0] for call in engine.log.call_args_list]
    assert any("Verbrennung Rang 3" in log for log in log_calls)

def test_poison_effect(engine_with_char):
    """Test: Vergiftung verursacht Direktschaden."""
    engine, char = engine_with_char
    char.add_status(StatusEffectType.POISON, duration=1, rank=5)
    
    engine.next_turn()

    # Rang 5 Vergiftung = 5 Direktschaden
    assert char.lp == 45
    assert len(char.status) == 0 # Dauer war 1, jetzt 0 -> Effekt entfernt
    log_calls = [call.args[0] for call in engine.log.call_args_list]
    assert any("Vergiftung Rang 5" in log for log in log_calls)

def test_bleeding_effect(engine_with_char):
    """Test: Blutungsschaden steigt pro Runde."""
    engine, char = engine_with_char
    char.add_status(StatusEffectType.BLEED, duration=2, rank=2)

    # Runde 1: Schaden = Rang/2 + 0 = 1
    engine.next_turn()
    assert char.lp == 49

    # Runde 2: Schaden = Rang/2 + 1 = 2
    engine.next_turn()
    assert char.lp == 47 # 49 - 2

def test_stun_effect(engine_with_char):
    """Test: Betäubung setzt skip_turns und wird im nächsten Zug verarbeitet."""
    engine, char = engine_with_char
    char.add_status(StatusEffectType.STUN, duration=1, rank=1)
    
    # next_turn() wird aufgerufen, der Charakter ist betäubt
    # Die Methode sollte den Skip erkennen und zum nächsten Zug springen (was hier das Ende ist)
    engine.next_turn()
    
    assert char.skip_turns == 0 # Wurde in _update_character_status verarbeitet
    log_calls = [call.args[0] for call in engine.log.call_args_list]
    assert any("ist betäubt" in log for log in log_calls)
    assert any("setzt aus" in log for log in log_calls)

def test_erosion_effect(engine_with_char):
    """Test: Erosion reduziert Max LP."""
    engine, char = engine_with_char
    max_lp_start = char.max_lp
    char.add_status(StatusEffectType.EROSION, duration=1, rank=1)
    
    with patch('random.randint', return_value=4): # Mock den Zufallswert
        engine.next_turn()

    assert char.max_lp == max_lp_start - 4 # 1 * 4
    # Erosion verursacht auch Direktschaden in Höhe des MaxLP Verlusts
    assert char.lp == 50 - 4

def test_add_status(engine_with_char):
    """Test: Status wird korrekt hinzugefügt."""
    _, char = engine_with_char
    char.add_status("Vergiftung", duration=3, rank=2)
    assert len(char.status) == 1
    assert char.status[0].name == "Vergiftung"
    assert char.status[0].duration == 3
    assert char.status[0].rank == 2
