import pytest
from unittest.mock import MagicMock
from src.controllers.combat_action_handler import CombatActionHandler
from src.models.character import Character
from src.models.enums import EventType

@pytest.fixture
def handler_setup():
    engine = MagicMock()
    history = MagicMock()
    view = MagicMock()

    # Setup characters list for engine
    engine.characters = []

    handler = CombatActionHandler(engine, history, lambda: view)
    return handler, engine, history, view

def test_roll_initiative_all(handler_setup):
    """Testet das Würfeln der Initiative für alle."""
    handler, engine, history, view = handler_setup

    c1 = Character("A", 10, 10, 10, 10)
    engine.characters = [c1]

    handler.roll_initiative_all()

    history.save_snapshot.assert_called_once()
    engine.roll_initiatives.assert_called_once()
    engine.notify.assert_called()

def test_next_turn(handler_setup):
    """Testet den Zugwechsel."""
    handler, engine, history, view = handler_setup

    handler.next_turn()

    history.save_snapshot.assert_called_once()
    engine.next_turn.assert_called_once()

def test_deal_damage_valid(handler_setup):
    """Testet das Austeilen von Schaden."""
    handler, engine, history, view = handler_setup

    # Setup selected character
    char = Character("Target", 20, 0, 0, 10)
    char.id = "uuid-1"
    engine.get_character_by_id.return_value = char
    view.get_selected_char_id.return_value = "uuid-1"
    view.get_action_value.return_value = 5
    view.get_action_type.return_value = "Normal"
    view.get_status_input.return_value = {"rank": "1"}

    handler.deal_damage()

    history.save_snapshot.assert_called_once()
    # Verify engine was called with correct parameters
    engine.apply_damage.assert_called_once_with(char, 5, "Normal", 1)

def test_deal_damage_invalid_value(handler_setup):
    """Testet Schaden mit ungültigem Wert."""
    handler, engine, history, view = handler_setup

    view.get_selected_char_id.return_value = "uuid-1"
    view.get_action_value.return_value = 0 # Invalid

    handler.deal_damage()

    history.save_snapshot.assert_not_called()
    view.show_info.assert_called()

def test_apply_healing(handler_setup):
    """Testet Heilung."""
    handler, engine, history, view = handler_setup

    char = Character("Target", 20, 0, 0, 10)
    char.lp = 10
    char.id = "uuid-1"
    engine.get_character_by_id.return_value = char
    view.get_selected_char_id.return_value = "uuid-1"
    view.get_action_value.return_value = 5

    handler.apply_healing()

    # Verify engine was called
    engine.apply_healing.assert_called_once_with(char, 5)
    history.save_snapshot.assert_called_once()

