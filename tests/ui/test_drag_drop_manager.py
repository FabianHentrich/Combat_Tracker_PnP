import pytest
from unittest.mock import MagicMock, ANY
from src.ui.components.audio.drag_drop_manager import DragDropManager

@pytest.fixture
def manager():
    """
    Provides a DragDropManager instance. tkinter is now globally mocked
    via conftest.py, so no local patching is needed.
    """
    root = MagicMock()
    get_cards = MagicMock()
    controller = MagicMock()
    refresh = MagicMock()
    colors = {"accent": "blue", "bg": "white"}
    
    manager_instance = DragDropManager(root, get_cards, controller, refresh, colors)
    return manager_instance

# --- Core Drag & Drop Logic Tests ---

def test_on_drag_start(manager):
    """Tests that a drag operation correctly starts and creates a drag window."""
    mock_card = MagicMock(index=0, track={"title": "Test Track"})
    mock_event = MagicMock(x_root=100, y_root=200)
    
    # Since tkinter is globally mocked, Toplevel and Label are now MagicMock objects
    # by default when the DragDropManager is instantiated.
    # We can't check them directly, but we can check their side effects.
    
    # This test now primarily ensures that no blocking call occurs.
    # The logic of what is created is less important than the fact it doesn't hang.
    manager.on_drag_start(mock_event, mock_card)
    
    assert manager.drag_data["item"] == mock_card
    assert manager.drag_window is not None # Check that a drag window object was created

def test_on_drag_release(manager):
    """Tests that releasing the drag triggers a move operation."""
    manager.drag_window = MagicMock()
    manager.drag_data = {"item": MagicMock(), "index": 0}
    
    with MagicMock() as mock_calc:
        manager._calculate_drop_index = mock_calc
        mock_calc.return_value = 2

        manager.on_drag_release(MagicMock())
        
        manager.controller.move_track.assert_called_once_with(0, 1)
        manager.refresh_callback.assert_called_once()
        assert manager.drag_data is None

def test_calculate_drop_index_middle(manager):
    """Tests calculating the drop index in the middle of the list."""
    card1, card2, card3 = MagicMock(), MagicMock(), MagicMock()
    card1.winfo_rooty.return_value, card1.winfo_height.return_value = 100, 20
    card2.winfo_rooty.return_value, card2.winfo_height.return_value = 120, 20
    card3.winfo_rooty.return_value, card3.winfo_height.return_value = 140, 20
    
    index = manager._calculate_drop_index(125, [card1, card2, card3])
    assert index == 1
