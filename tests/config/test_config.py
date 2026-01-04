import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# sys.path.append removed. Run tests with python -m pytest

from src.config import load_hotkeys

# Die Tests für load_rules wurden entfernt, da die Funktion nicht mehr existiert
# und die Logik nun im RuleManager liegt, der global gemockt wird.

def test_load_hotkeys_default():
    """
    Testet das Laden der Standard-Hotkeys, wenn keine hotkeys.json existiert.
    """
    with patch("os.path.exists", return_value=False):
        hotkeys = load_hotkeys("dummy.json")

        assert "next_turn" in hotkeys
        assert hotkeys["next_turn"] == "<space>"

def test_load_hotkeys_from_file():
    """
    Testet das Laden von Hotkeys aus einer JSON-Datei.
    """
    mock_data = {"next_turn": "<F1>"}
    json_data = json.dumps(mock_data)

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json_data)):
            hotkeys = load_hotkeys("dummy.json")

            assert hotkeys["next_turn"] == "<F1>"
