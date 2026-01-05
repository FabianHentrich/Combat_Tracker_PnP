import pytest
from unittest.mock import MagicMock, patch
from src.utils.localization import translate
from src.ui.components.dice_roller import DiceRoller

@pytest.fixture
def roller():
    """Provides a DiceRoller instance with mocked UI elements."""
    with patch.object(DiceRoller, '_create_ui'), \
         patch('tkinter.ttk.LabelFrame'), \
         patch('tkinter.StringVar'):
        # To test the logic, we don't need the real UI.
        # Wir ersetzen result_var und history_var durch Mocks mit gemockter set-Methode
        roller_instance = DiceRoller(parent=MagicMock(), colors={})
        roller_instance.result_var = MagicMock()
        roller_instance.result_var.set = MagicMock()
        roller_instance.history_var = MagicMock()
        roller_instance.history_var.set = MagicMock()
        yield roller_instance

# --- _finalize_roll Test ---

@patch('src.ui.components.dice_roller.roll_exploding_dice', return_value=(15, [10, 5]))
def test_finalize_roll(mock_roll, roller):
    """Tests that the final roll result is correctly displayed."""
    roller._finalize_roll(sides=10)
    
    # Check that the final result is set
    roller.result_var.set.assert_called_with("15")
    
    # Check that the history/log message is generated and set
    expected_msg = translate("dice_roller.result_exploded", sides=10, roll_str="10 + 5", total=15)
    roller.history_var.set.assert_called_with(expected_msg)
    
    # Check that the rolling state is reset
    assert roller.is_rolling is False

# --- roll_dice Test ---

def test_roll_dice_starts_animation(roller):
    """Tests that rolling a dice sets the state and starts the animation loop."""
    with patch.object(roller, '_animate_roll') as mock_animate:
        roller.is_rolling = False # Ensure initial state
        roller.roll_dice(sides=20)
        
        assert roller.is_rolling is True
        roller.history_var.set.assert_called_with("Rolling d20...")
        mock_animate.assert_called_once()

def test_roll_dice_blocked_if_already_rolling(roller):
    """Tests that a new roll cannot be started while another is in progress."""
    with patch.object(roller, '_animate_roll') as mock_animate:
        roller.is_rolling = True # Simulate an ongoing roll
        roller.roll_dice(sides=20)
        
        # The animation should not be called again
        mock_animate.assert_not_called()

# --- _get_roll_message Tests (existing tests are good) ---

def test_get_roll_message_exploded():
    """Tests the static message formatting for an exploding dice roll."""
    expected_message = translate("dice_roller.result_exploded", sides=6, roll_str="6 + 4", total=10)
    actual_message = DiceRoller._get_roll_message(6, 10, [6, 4])
    assert actual_message == expected_message

def test_get_roll_message_normal():
    """Tests the static message formatting for a normal (non-exploding) dice roll."""
    expected_message = translate("dice_roller.result_normal", sides=6, roll_str="3")
    actual_message = DiceRoller._get_roll_message(6, 3, [3])
    assert actual_message == expected_message
