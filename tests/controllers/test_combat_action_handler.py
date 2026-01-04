import pytest
from unittest.mock import MagicMock, patch
from src.controllers.combat_action_handler import CombatActionHandler
from src.models.character import Character

@pytest.fixture
def mock_deps():
    """Erstellt gemockte Abhängigkeiten für den CombatActionHandler."""
    engine = MagicMock()
    history = MagicMock()
    
    # Mock für die View erstellen, die das ICombatView-Interface implementiert
    view = MagicMock()
    
    # Die view_provider-Funktion gibt einfach den Mock zurück
    view_provider = lambda: view
    
    return engine, history, view_provider, view

def test_deal_damage_multiple_targets(mock_deps):
    """
    Testet, ob Schaden korrekt auf mehrere Ziele angewendet wird.
    """
    engine, history, view_provider, view = mock_deps
    handler = CombatActionHandler(engine, history, view_provider)

    # Zwei Charaktere erstellen und der Engine bekannt machen
    char1 = Character("Goblin", 10, 0, 0, 10, char_id="goblin_1")
    char2 = Character("Orc", 20, 0, 0, 5, char_id="orc_1")
    engine.get_character_by_id.side_effect = lambda cid: char1 if cid == "goblin_1" else char2

    # View so mocken, dass sie die IDs beider Charaktere zurückgibt
    view.get_selected_char_ids.return_value = ["goblin_1", "orc_1"]
    view.get_damage_data.return_value = (10, "10 Normal")
    view.get_status_input.return_value = {"rank": 1}

    handler.deal_damage()

    # Prüfen, ob der Snapshot gespeichert wurde
    history.save_snapshot.assert_called_once()
    
    # Prüfen, ob apply_damage für BEIDE Charaktere aufgerufen wurde
    assert engine.apply_damage.call_count == 2
    engine.apply_damage.assert_any_call(char1, 10, "Normal", 1)
    engine.apply_damage.assert_any_call(char2, 10, "Normal", 1)
    
    # Prüfen, ob eine Log-Nachricht für mehrere Ziele gesendet wurde
    engine.log.assert_called_with("Schaden auf 2 Ziele angewendet.")

def test_deal_damage_single_target(mock_deps):
    """
    Testet, ob Schaden korrekt auf ein einzelnes Ziel angewendet wird.
    """
    engine, history, view_provider, view = mock_deps
    handler = CombatActionHandler(engine, history, view_provider)

    char1 = Character("Goblin", 10, 0, 0, 10, char_id="goblin_1")
    engine.get_character_by_id.return_value = char1

    view.get_selected_char_ids.return_value = ["goblin_1"]
    view.get_damage_data.return_value = (5, "5 Feuer")
    view.get_status_input.return_value = {"rank": 2}

    handler.deal_damage()

    history.save_snapshot.assert_called_once()
    
    # Prüfen, ob apply_damage genau einmal aufgerufen wurde
    engine.apply_damage.assert_called_once_with(char1, 5, "Feuer", 2)

def test_deal_damage_no_target(mock_deps):
    """
    Testet das Verhalten, wenn kein Ziel ausgewählt ist.
    """
    engine, history, view_provider, view = mock_deps
    handler = CombatActionHandler(engine, history, view_provider)

    # View so mocken, dass sie eine leere Liste zurückgibt
    view.get_selected_char_ids.return_value = []

    handler.deal_damage()

    # Es darf keine Aktion ausgeführt werden
    history.save_snapshot.assert_not_called()
    engine.apply_damage.assert_not_called()
    
    # Stattdessen sollte eine Fehlermeldung angezeigt werden
    view.show_error.assert_called_once_with("Fehler", "Kein Charakter ausgewählt.")

def test_add_status_multiple_targets(mock_deps):
    """
    Testet das Hinzufügen von Status-Effekten zu mehreren Zielen.
    """
    engine, history, view_provider, view = mock_deps
    handler = CombatActionHandler(engine, history, view_provider)

    char1 = Character("Goblin", 10, 0, 0, 10, char_id="goblin_1")
    char2 = Character("Orc", 20, 0, 0, 5, char_id="orc_1")
    engine.get_character_by_id.side_effect = lambda cid: char1 if cid == "goblin_1" else char2

    view.get_selected_char_ids.return_value = ["goblin_1", "orc_1"]
    view.get_status_input.return_value = {"status": "Vergiftung", "duration": "3", "rank": "2"}

    handler.add_status_to_character()

    history.save_snapshot.assert_called_once()
    
    # Prüfen, ob add_status_effect für beide Charaktere aufgerufen wurde
    assert engine.add_status_effect.call_count == 2
    engine.add_status_effect.assert_any_call(char1, "Vergiftung", 3, 2)
    engine.add_status_effect.assert_any_call(char2, "Vergiftung", 3, 2)

    engine.log.assert_called_with("Status 'Vergiftung' auf 2 Ziele angewendet.")
