import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.controllers.library_import_tab import LibraryImportTab
from src.models.enums import CharacterType

@pytest.fixture
def mock_deps():
    """Provides common mocked dependencies for the tab controller."""
    parent = MagicMock()
    engine = MagicMock()
    history_manager = MagicMock()
    colors = {"bg": "#FFF", "fg": "#000", "panel": "#EEE"}
    close_callback = MagicMock()
    return parent, engine, history_manager, colors, close_callback

@pytest.fixture
def tab(mock_deps):
    """
    Provides a LibraryImportTab instance with a fully mocked UI structure.
    This is essential as the controller builds its UI upon initialization.
    """
    # Patch the UI components that would be created in setup_ui
    with patch('tkinter.ttk.Treeview') as mock_tree_cls, \
         patch('tkinter.ttk.Entry'), \
         patch('tkinter.ttk.Combobox'), \
         patch('tkinter.ttk.Checkbutton'), \
         patch('tkinter.ttk.Button'), \
         patch('tkinter.ttk.Label'), \
         patch('tkinter.Canvas'), \
         patch('src.controllers.library_import_tab.EnemyDataLoader') as mock_data_loader:

        # Configure the data loader mock
        mock_loader_instance = mock_data_loader.return_value
        mock_loader_instance.get_all_presets.return_value = {"Goblins": {"Goblin": {"lp": 10, "rp": 2, "sp": 0, "gew": 2, "level": 1}}}
        mock_loader_instance.flat_presets = {"Goblin": {"lp": 10, "rp": 2, "sp": 0, "gew": 2, "level": 1}}

        # Instantiate the tab controller
        t = LibraryImportTab(*mock_deps)
        # The tree is created inside setup_ui, so we assign our mock instance to the attribute
        t.tree = mock_tree_cls.return_value
        yield t

def _create_mock_staging_entry(name="Test", type_val=CharacterType.ENEMY.value, lp="10", rp="5", sp="0", gew="1", level="0", count="1", surprise=False):
    """Helper to create a mock for a single staging entry's widgets."""
    return {
        "name": MagicMock(get=MagicMock(return_value=name)),
        "type": MagicMock(get=MagicMock(return_value=type_val)),
        "lp": MagicMock(get=MagicMock(return_value=lp)),
        "rp": MagicMock(get=MagicMock(return_value=rp)),
        "sp": MagicMock(get=MagicMock(return_value=sp)),
        "gew": MagicMock(get=MagicMock(return_value=gew)),
        "level": MagicMock(get=MagicMock(return_value=level)),
        "count": MagicMock(get=MagicMock(return_value=count)),
        "surprise": MagicMock(get=MagicMock(return_value=surprise)),
        "translated_types": {CharacterType.ENEMY.value: CharacterType.ENEMY.value} # Simplified for test
    }

# --- Tests ---

def test_on_search_change_filters_tree(tab):
    """Tests that searching filters the tree view correctly."""
    tab.search_var.get.return_value = "goblin"
    # Simulate that the tree has items to be deleted
    tab.tree.get_children.return_value = ["I001"]

    with patch.object(tab, 'populate_tree') as mock_populate, \
         patch.object(tab, '_expand_all_nodes') as mock_expand:

        tab.on_search_change()

        # Check that the tree is cleared and repopulated
        tab.tree.delete.assert_called_with("I001")
        mock_populate.assert_called_once()
        mock_expand.assert_called_once()

def test_search_returns_hit_count(tab):
    """Tests that the search method returns the number of found items."""
    tab.tree.get_children.return_value = ["I001", "I002"] # Simulate two items in the tree
    count = tab.search("goblin")
    assert count == 2

def test_add_selected_to_staging_enemy(tab):
    """Tests that selecting an enemy adds it to the staging area."""
    tab.tree.selection.return_value = ["I001"]
    tab.tree.item.side_effect = lambda item_id, opt: "Goblin" if opt == "text" else ("enemy",)

    with patch.object(tab, 'add_staging_row') as mock_add_row:
        tab.add_selected_to_staging()
        mock_add_row.assert_called_once_with("Goblin", tab.flat_presets["Goblin"])

def test_add_selected_to_staging_category(tab):
    """Tests that selecting a category does nothing."""
    tab.tree.selection.return_value = ["I001"]
    tab.tree.item.side_effect = lambda item_id, opt: "Goblins" if opt == "text" else ("category",)

    with patch.object(tab, 'add_staging_row') as mock_add_row:
        tab.add_selected_to_staging()
        mock_add_row.assert_not_called()

def test_finalize_import_success_multiple(tab):
    """Tests importing multiple characters with name suffixes."""
    tab.staging_entries = [_create_mock_staging_entry(name="Orc", count="3")]

    with patch('src.controllers.library_import_tab.wuerfle_initiative', return_value=10):
        tab.finalize_import()

    assert tab.engine.insert_character.call_count == 3
    # Check that names are suffixed correctly
    first_call_name = tab.engine.insert_character.call_args_list[0].args[0].name
    third_call_name = tab.engine.insert_character.call_args_list[2].args[0].name
    assert first_call_name == "Orc 1"
    assert third_call_name == "Orc 3"

@patch('src.controllers.library_import_tab.messagebox.showerror')
def test_finalize_import_value_error(mock_showerror, tab):
    """Tests that an error is shown for invalid staging data."""
    # Mock an entry with non-numeric LP
    tab.staging_entries = [_create_mock_staging_entry(lp="abc")]
    
    tab.finalize_import()

    mock_showerror.assert_called_once()
    tab.engine.insert_character.assert_not_called()

def test_remove_staging_row(tab):
    """Tests removing a row from the staging area."""
    mock_frame = MagicMock()
    entry_obj = {"frame": mock_frame}
    tab.staging_entries = [entry_obj]

    tab.remove_staging_row(mock_frame, entry_obj)

    mock_frame.destroy.assert_called_once()
    assert len(tab.staging_entries) == 0
