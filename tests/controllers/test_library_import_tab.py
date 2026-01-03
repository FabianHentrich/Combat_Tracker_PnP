import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.controllers.library_import_tab import LibraryImportTab
from src.models.enums import CharacterType

@pytest.fixture
def mock_dependencies():
    parent = MagicMock()
    engine = MagicMock()
    history_manager = MagicMock()
    colors = {"panel": "grey"}
    close_callback = MagicMock()
    return parent, engine, history_manager, colors, close_callback

@patch("src.controllers.library_import_tab.EnemyDataLoader")
def test_finalize_import_limits_gew(MockLoader, mock_dependencies):
    parent, engine, history_manager, colors, close_callback = mock_dependencies

    # Mock loader
    loader_instance = MockLoader.return_value
    loader_instance.get_all_presets.return_value = {}
    loader_instance.flat_presets = {}

    # Initialize tab
    # We need to mock UI creation parts that might fail without a real tk root
    with patch("tkinter.ttk.PanedWindow"), \
         patch("tkinter.ttk.Frame"), \
         patch("tkinter.ttk.Label"), \
         patch("tkinter.ttk.Entry"), \
         patch("tkinter.ttk.Treeview"), \
         patch("tkinter.ttk.Scrollbar"), \
         patch("tkinter.ttk.Button"), \
         patch("tkinter.Canvas"), \
         patch("tkinter.StringVar"):

        tab = LibraryImportTab(parent, engine, history_manager, colors, close_callback)

    # Manually add a staging entry with GEW > 6
    entry_obj = {
        "name": MagicMock(),
        "type": MagicMock(),
        "lp": MagicMock(),
        "rp": MagicMock(),
        "sp": MagicMock(),
        "gew": MagicMock(),
        "level": MagicMock(),
        "count": MagicMock(),
        "surprise": MagicMock()
    }

    entry_obj["name"].get.return_value = "Boss"
    entry_obj["type"].get.return_value = CharacterType.ENEMY.value
    entry_obj["lp"].get.return_value = "100"
    entry_obj["rp"].get.return_value = "10"
    entry_obj["sp"].get.return_value = "0"
    entry_obj["gew"].get.return_value = "10" # Should be capped
    entry_obj["level"].get.return_value = "5"
    entry_obj["count"].get.return_value = "1"
    entry_obj["surprise"].get.return_value = False

    tab.staging_entries.append(entry_obj)

    # Execute
    tab.finalize_import()

    # Verify
    engine.insert_character.assert_called_once()
    args, _ = engine.insert_character.call_args
    new_char = args[0]

    assert new_char.gew == 6
