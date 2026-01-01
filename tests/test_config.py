import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# sys.path.append removed. Run tests with python -m pytest

from src.utils.config import load_rules, load_hotkeys

def test_load_rules_default():
    """
    Testet das Laden der Standard-Regeln, wenn keine rules.json existiert.
    Überprüft, ob die Standard-Schlüssel vorhanden sind.
    """
    with patch("os.path.exists", return_value=False):
        rules, dmg_desc, status_desc = load_rules("dummy.json")

        assert "damage_types" in rules
        assert "status_effects" in rules
        assert "Normal" in rules["damage_types"]
        assert "Vergiftung" in rules["status_effects"]

def test_load_rules_from_file():
    """
    Testet das Laden von Regeln aus einer JSON-Datei.
    Überprüft, ob die geladenen Werte korrekt übernommen werden.
    """
    mock_data = {
        "damage_types": {
            "TestDmg": {"description": "Test", "ignores_armor": True}
        },
        "status_effects": {
            "TestStatus": {"description": "Test", "max_rank": 1}
        }
    }
    json_data = json.dumps(mock_data)

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json_data)):
            rules, dmg_desc, status_desc = load_rules("dummy.json")

            assert "TestDmg" in rules["damage_types"]
            assert "TestStatus" in rules["status_effects"]
            assert dmg_desc["TestDmg"] == "Test"

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
