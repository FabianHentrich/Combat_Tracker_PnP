import pytest
from unittest.mock import MagicMock, patch

# Mock tkinter before import
@patch('tkinter.ttk.Frame')
def get_character_list(MockFrame):
    from src.ui.components.combat.character_list import CharacterList
    
    mock_controller = MagicMock()
    mock_controller.engine = MagicMock()
    
    with patch.object(CharacterList, '_setup_ui'):
        cl = CharacterList(parent=MagicMock(), controller=mock_controller, colors={})
        cl.tree = MagicMock()
    return cl

@pytest.fixture
def char_list():
    """Provides a CharacterList instance with mocked UI elements."""
    return get_character_list()

def _create_mock_char(name, lp, max_lp, init):
    """Helper to create a mock character."""
    char = MagicMock()
    char.id = name # Use name as ID for simplicity in tests
    char.name = name
    char.lp = lp
    char.max_lp = max_lp
    char.init = init
    char.get_status_string.return_value = ""
    return char

# --- update_list Tests ---

def test_update_list_sorting_order(char_list):
    """Tests that the list is correctly sorted with the current character on top."""
    # Setup characters
    chars = [
        _create_mock_char("A", 10, 10, 20),
        _create_mock_char("B", 10, 10, 15),
        _create_mock_char("C", 10, 10, 10)
    ]
    char_list.controller.engine.characters = chars
    char_list.controller.engine.initiative_rolled = True
    char_list.controller.engine.turn_index = 1 # It's B's turn

    char_list.update_list()

    # The display order should be B, C, A
    insert_calls = char_list.tree.insert.call_args_list
    assert len(insert_calls) == 3
    
    # Check the 'values' tuple passed to insert, where the name is at index 1
    assert insert_calls[0].kwargs['values'][1] == "B"
    assert insert_calls[1].kwargs['values'][1] == "C"
    assert insert_calls[2].kwargs['values'][1] == "A"

def test_update_list_tagging(char_list):
    """Tests that 'dead' and 'low_hp' tags are correctly applied."""
    chars = [
        _create_mock_char("DeadChar", 0, 10, 20),
        _create_mock_char("LowHpChar", 2, 10, 15), # 20% HP
        _create_mock_char("HealthyChar", 10, 10, 10)
    ]
    char_list.controller.engine.characters = chars
    char_list.controller.engine.initiative_rolled = False # Order doesn't matter here

    char_list.update_list()

    # Check the tags applied via tree.item()
    item_calls = char_list.tree.item.call_args_list
    
    # Find the calls for each character based on their ID
    dead_char_call = next(c for c in item_calls if c.args[0] == "DeadChar")
    low_hp_char_call = next(c for c in item_calls if c.args[0] == "LowHpChar")
    healthy_char_call = next(c for c in item_calls if c.args[0] == "HealthyChar")

    assert 'dead' in dead_char_call.kwargs['tags']
    assert 'low_hp' in low_hp_char_call.kwargs['tags']
    # Healthy char might not have a call to item() if it has no tags, which is correct.
    # Or it might be called with tags=().
    if healthy_char_call:
        assert 'tags' not in healthy_char_call.kwargs or healthy_char_call.kwargs['tags'] == ()

def test_update_list_restores_selection(char_list):
    """Tests that the selection is restored after the list is updated."""
    chars = [_create_mock_char("A", 10, 10, 20)]
    char_list.controller.engine.characters = chars
    
    # Simulate a pre-existing selection
    char_list.tree.selection.return_value = ["A"]
    # Simulate that the item still exists after re-insertion
    char_list.tree.exists.return_value = True
    
    char_list.update_list()
    
    # Check that selection_set was called to restore the selection
    char_list.tree.selection_set.assert_called_once_with(["A"])

# --- Other Method Tests ---

def test_get_selected_ids(char_list):
    """Tests that the get_selected_ids method returns the tree's selection."""
    char_list.tree.selection.return_value = ("char1_id", "char2_id")
    
    ids = char_list.get_selected_ids()
    
    assert ids == ["char1_id", "char2_id"]

def test_show_context_menu(char_list):
    """Tests that the context menu selects the item before appearing."""
    char_list.context_menu = MagicMock()
    mock_event = MagicMock()
    
    # Simulate right-clicking a row that is not currently selected
    char_list.tree.identify_row.return_value = "item_to_select"
    char_list.tree.selection.return_value = ("a_different_item",)
    
    char_list.show_context_menu(mock_event)
    
    # The selection should be changed to the clicked item
    char_list.tree.selection_set.assert_called_once_with("item_to_select")
    char_list.context_menu.post.assert_called_once()
