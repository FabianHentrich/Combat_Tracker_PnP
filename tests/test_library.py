import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.library_handler import LibraryHandler

def test_library_window_creation():
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

