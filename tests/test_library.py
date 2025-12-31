import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.library_handler import LibraryHandler

def test_library_window_creation():
    """
    Testet das Öffnen des Bibliotheks-Fensters.
    Überprüft, ob das Fenster erstellt und der Treeview mit Daten gefüllt wird.
    """
    tracker = MagicMock()
    tracker.enemy_presets_structure = {
        "Bosses": {
            "Big Boss": {"lp": 100}
        },
        "Minions": {
            "Small Minion": {"lp": 10}
        }
    }
    tracker.enemy_presets = {
        "Big Boss": {"lp": 100},
        "Small Minion": {"lp": 10}
    }

    root = MagicMock()
    colors = {"bg": "black", "panel": "gray"}

    handler = LibraryHandler(tracker, root, colors)

    # Patch 'src.library_handler.tk' to mock tkinter used in that module
    with patch('src.library_handler.tk') as mock_tk, \
         patch('src.library_handler.ttk') as mock_ttk:

        # Setup mock for Treeview
        mock_tree = MagicMock()
        mock_ttk.Treeview.return_value = mock_tree

        handler.open_library_window()

        assert mock_tk.Toplevel.called

        # Check if tree was populated
        assert handler.tree.insert.called

        # We can inspect call_args_list
        calls = handler.tree.insert.call_args_list
        assert len(calls) >= 2

def test_add_to_staging():
    """
    Testet das Hinzufügen eines Gegners zur Staging-Area (Vorbereitung).
    Überprüft, ob der Eintrag in der Staging-Liste erscheint und UI-Elemente erstellt werden.
    """
    tracker = MagicMock()
    tracker.enemy_presets = {"Goblin": {"lp": 7, "type": "Gegner"}}

    handler = LibraryHandler(tracker, MagicMock(), {})
    handler.scrollable_frame = MagicMock()

    # Mock tree selection
    handler.tree = MagicMock()
    handler.tree.selection.return_value = ["item1"]

    def mock_tree_item(item, option):
        if option == "text": return "Goblin"
        if option == "tags": return ("enemy",)
        return None

    handler.tree.item.side_effect = mock_tree_item

    # Patch ttk in library_handler for Entry and Combobox
    with patch('src.library_handler.ttk') as mock_ttk:
        handler.add_selected_to_staging()

        assert len(handler.staging_entries) == 1
        # Check if Entry was created (mock_ttk.Entry called)
        assert mock_ttk.Entry.called

def test_library_search():
    """
    Testet die Suchfunktion der Bibliothek.
    Überprüft, ob die Daten korrekt gefiltert werden.
    """
    tracker = MagicMock()
    # Struktur: Kategorie -> Unterkategorie -> Gegner
    tracker.enemy_presets_structure = {
        "Gruppe A": {
            "Gegner 1": {"lp": 10},
            "Gegner 2": {"lp": 20}
        },
        "Gruppe B": {
            "Boss": {"lp": 100}
        }
    }

    handler = LibraryHandler(tracker, MagicMock(), {})

    # Test 1: Suche nach "Boss"
    filtered = handler._filter_data_recursive(tracker.enemy_presets_structure, "boss")
    assert "Gruppe B" in filtered
    assert "Boss" in filtered["Gruppe B"]
    assert "Gruppe A" not in filtered

    # Test 2: Suche nach "Gegner"
    filtered = handler._filter_data_recursive(tracker.enemy_presets_structure, "gegner")
    assert "Gruppe A" in filtered
    assert "Gegner 1" in filtered["Gruppe A"]
    assert "Gegner 2" in filtered["Gruppe A"]
    assert "Gruppe B" not in filtered

    # Test 3: Suche ohne Treffer
    filtered = handler._filter_data_recursive(tracker.enemy_presets_structure, "xyz")
    assert len(filtered) == 0
