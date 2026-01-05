import pytest
from unittest.mock import MagicMock, patch
from src.controllers.combat_action_handler import CombatActionHandler
from src.models.character import Character
from src.models.enums import ScopeType
from src.utils.localization import translate

@pytest.fixture
def mock_dependencies():
    """Provides a fixture for all dependencies of CombatActionHandler."""
    engine = MagicMock()
    history_manager = MagicMock()
    view = MagicMock()
    return engine, history_manager, view

@pytest.fixture
def handler(mock_dependencies):
    """Provides a CombatActionHandler instance with mocked dependencies."""
    return CombatActionHandler(*mock_dependencies)

@pytest.fixture
def sample_character():
    """Provides a sample character for testing."""
    char = Character(name="TestChar", lp=50, rp=10, sp=5, init=15)
    char.id = "char1"
    return char

# --- Tests ---

def test_roll_initiative_all(handler):
    """Tests that initiative is rolled for all characters."""
    handler.engine.characters = [MagicMock()] # Simulate at least one character
    handler.roll_initiative_all()
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.roll_initiatives.assert_called_once()
    handler.engine.notify.assert_called_once() # Check for log message

def test_reset_initiative(handler):
    """Tests resetting initiative for all characters."""
    handler.reset_initiative(ScopeType.ALL.value)
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.reset_initiative.assert_called_once_with(ScopeType.ALL.value)

def test_next_turn(handler):
    """Tests advancing to the next turn."""
    handler.next_turn()
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.next_turn.assert_called_once()

def test_deal_damage_no_selection(handler):
    """Tests that no action is taken if no character is selected."""
    handler.view.get_selected_char_ids.return_value = []
    handler.deal_damage()
    handler.view.show_error.assert_called_once_with(translate("dialog.error.title"), translate("messages.no_character_selected"))
    handler.engine.apply_damage.assert_not_called()

def test_deal_damage_zero_damage(handler):
    """Tests that an info message is shown for zero damage."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.view.get_damage_data.return_value = (0, "1W6 Normal")
    handler.deal_damage()
    handler.view.show_info.assert_called_once_with(translate("dialog.info.title"), translate("messages.enter_damage_value"))

def test_deal_damage_successful(handler, sample_character):
    """Tests successful damage application to a selected character."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.engine.get_character_by_id.return_value = sample_character
    handler.view.get_damage_data.return_value = (10, "1W6+2 Fire")
    handler.view.get_status_input.return_value = {"rank": "2"}
    
    handler.deal_damage()
    
    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.apply_damage.assert_called_once_with(sample_character, 10, "Fire", 2, "1W6+2 Fire")

def test_add_status_no_selection(handler):
    """Tests that status is not added if no character is selected."""
    handler.view.get_selected_char_ids.return_value = []
    handler.add_status_to_character()
    handler.view.show_error.assert_called_once_with(translate("dialog.error.title"), translate("messages.no_character_selected"))

def test_add_status_invalid_input(handler):
    """Tests that a warning is shown for invalid duration/rank."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.view.get_status_input.return_value = {"status": "Burning", "duration": "abc", "rank": "1"}
    handler.add_status_to_character()
    handler.view.show_warning.assert_called_once_with(translate("dialog.error.title"), translate("messages.enter_valid_numbers_duration_rank"))

def test_add_status_successful(handler, sample_character):
    """Tests successful status effect application."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.engine.get_character_by_id.return_value = sample_character
    handler.view.get_status_input.return_value = {"status": "Burning", "duration": "3", "rank": "2"}
    
    with patch('src.controllers.combat_action_handler.get_rules') as mock_get_rules:
        mock_get_rules.return_value = {
            "status_effects": {"Burning": {"max_rank": 6}}
        }
        handler.add_status_to_character()

    handler.history_manager.save_snapshot.assert_called_once()
    handler.engine.add_status_effect.assert_called_once_with(sample_character, "Burning", 3, 2)

@pytest.mark.parametrize("method_name, info_message", [
    ("apply_healing", translate("messages.enter_healing_value")),
])
def test_action_zero_value(handler, method_name, info_message):
    """Tests that actions show info if the input value is zero or less."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.view.get_action_value.return_value = 0

    action_method = getattr(handler, method_name)
    action_method()

    handler.view.show_info.assert_called_once_with(translate("dialog.info.title"), info_message)

@pytest.mark.parametrize("method_name", ["apply_shield", "apply_armor"])
def test_positive_value_actions(handler, sample_character, method_name):
    """Tests actions that only trigger with a positive value (shield, armor)."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.engine.get_character_by_id.return_value = sample_character
    handler.view.get_action_value.return_value = 5

    action_method = getattr(handler, method_name)
    action_method()

    handler.history_manager.save_snapshot.assert_called_once()
    engine_method = getattr(handler.engine, method_name)
    engine_method.assert_called_once_with(sample_character, 5)

@pytest.mark.parametrize("method_name", ["apply_shield", "apply_armor"])
def test_zero_value_actions_no_effect(handler, method_name):
    """Tests that shield/armor actions have no effect with zero value."""
    handler.view.get_selected_char_ids.return_value = ["char1"]
    handler.view.get_action_value.return_value = 0

    action_method = getattr(handler, method_name)
    action_method()

    handler.history_manager.save_snapshot.assert_not_called()
    engine_method = getattr(handler.engine, method_name)
    engine_method.assert_not_called()
