import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
import sys
import importlib
from src.dice_roller import DiceRoller

# Mock Tkinter root for the DiceRoller init
@pytest.fixture
def mock_root():
    root = MagicMock()
    return root

@pytest.fixture(autouse=True)
def clean_imports():
    # Force cleanup of mocked tkinter from other tests
    if 'tkinter' in sys.modules and isinstance(sys.modules['tkinter'], MagicMock):
        del sys.modules['tkinter']
    if 'tkinter.ttk' in sys.modules and isinstance(sys.modules['tkinter.ttk'], MagicMock):
        del sys.modules['tkinter.ttk']

    # Ensure we have a clean src.dice_roller
    if 'src.dice_roller' in sys.modules:
        importlib.reload(sys.modules['src.dice_roller'])
    else:
        import src.dice_roller
    yield

def test_dice_roller_integration(mock_root):
    import src.dice_roller
    print(f"DEBUG: tkinter in sys.modules: {'tkinter' in sys.modules}")
    if 'tkinter' in sys.modules:
        print(f"DEBUG: tkinter is {sys.modules['tkinter']}")
    print(f"DEBUG: DiceRoller is {src.dice_roller.DiceRoller}")

    # We need to mock the UI creation parts because they require a real tk environment
    with patch('src.dice_roller.DiceRoller._create_ui'), \
         patch('tkinter.ttk.LabelFrame'), \
         patch('tkinter.StringVar'), \
         patch('src.dice_roller.roll_exploding_dice', return_value=(10, [6, 4])) as mock_roll:

        roller = DiceRoller(mock_root)
        # Mock the StringVars since we patched the class but need instances on the object
        roller.result_var = MagicMock()
        roller.history_var = MagicMock()

        roller._finalize_roll(6)

        mock_roll.assert_called_once_with(6)
        roller.result_var.set.assert_called_with("10")

        # Check history string format
        # "W6: 6 + 4 = 10 (Explodiert!)"
        args, _ = roller.history_var.set.call_args
        assert "W6: 6 + 4 = 10 (Explodiert!)" in args[0]

def test_dice_roller_no_explosion(mock_root):
     with patch('src.dice_roller.DiceRoller._create_ui'), \
         patch('tkinter.ttk.LabelFrame'), \
         patch('tkinter.StringVar'), \
         patch('src.dice_roller.roll_exploding_dice', return_value=(3, [3])) as mock_roll:

        roller = DiceRoller(mock_root)
        roller.result_var = MagicMock()
        roller.history_var = MagicMock()

        roller._finalize_roll(6)

        mock_roll.assert_called_once_with(6)
        roller.result_var.set.assert_called_with("3")

        args, _ = roller.history_var.set.call_args
        assert "W6: 3" in args[0]

