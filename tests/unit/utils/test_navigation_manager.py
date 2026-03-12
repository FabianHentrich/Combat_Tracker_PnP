import pytest
from unittest.mock import MagicMock
from src.utils.navigation_manager import NavigationManager
from src.config import MAX_HISTORY

@pytest.fixture
def nav_manager():
    """Provides a NavigationManager with mocked callbacks for each test."""
    restore_mock = MagicMock()
    ui_update_mock = MagicMock()
    return NavigationManager(restore_mock, ui_update_mock), restore_mock, ui_update_mock

# --- Core Logic Tests ---

def test_push_and_restore(nav_manager):
    """Tests adding states and navigating back and forward."""
    nav, restore_mock, _ = nav_manager
    state1, state2 = {"id": 1}, {"id": 2}

    nav.push(state1)
    nav.push(state2)

    assert nav.index == 1
    assert len(nav.history) == 2

    nav.back()
    assert nav.index == 0
    restore_mock.assert_called_with(state1)

    nav.forward()
    assert nav.index == 1
    restore_mock.assert_called_with(state2)

def test_history_limit(nav_manager):
    """Tests that the history stack does not exceed MAX_HISTORY."""
    nav, _, _ = nav_manager
    # Use a smaller limit for the test to run faster
    nav.max_history = 2 

    for i in range(5):
        nav.push({"id": i})

    assert len(nav.history) == 2
    assert nav.history[0]["id"] == 3 # First element should be the 4th pushed state
    assert nav.history[1]["id"] == 4 # Last element should be the 5th pushed state

def test_overwrite_future_on_new_push(nav_manager):
    """Tests that future history is cleared when a new state is pushed after going back."""
    nav, _, _ = nav_manager
    nav.push({"id": 1})
    nav.push({"id": 2})
    nav.push({"id": 3})

    nav.back() # Index is now at {"id": 2}
    nav.push({"id": 4}) # This should erase {"id": 3}

    assert len(nav.history) == 3
    assert nav.history[-1]["id"] == 4
    assert nav.index == 2

# --- Edge Case and Callback Tests ---

def test_push_ignores_duplicates(nav_manager):
    """Tests that pushing the same state consecutively does not create a new entry."""
    nav, _, _ = nav_manager
    state = {"id": 1}
    
    nav.push(state)
    nav.push(state) # Push the exact same state again
    
    assert len(nav.history) == 1

def test_is_navigating_flag_prevents_push(nav_manager):
    """Tests that push is ignored while a restore operation is in progress."""
    nav, restore_mock, _ = nav_manager
    
    # Create a restore callback that tries to push a new state
    def restore_and_push(state):
        nav.push({"id": "recursive_push"})

    restore_mock.side_effect = restore_and_push
    nav.on_restore = restore_mock

    nav.push({"id": 1})
    nav.push({"id": 2})
    
    # This will trigger the malicious callback
    nav.back()
    
    # The history should not contain the recursive push
    assert len(nav.history) == 2
    assert not any(s["id"] == "recursive_push" for s in nav.history)

def test_ui_update_callback(nav_manager):
    """Tests that the UI update callback is called with correct boolean flags."""
    nav, _, ui_update_mock = nav_manager
    
    # Initial state
    ui_update_mock.assert_not_called()
    
    # 1. Push first item
    nav.push({"id": 1})
    # can_back=False, can_forward=False
    ui_update_mock.assert_called_with(False, False)
    
    # 2. Push second item
    nav.push({"id": 2})
    # can_back=True, can_forward=False
    ui_update_mock.assert_called_with(True, False)
    
    # 3. Go back
    nav.back()
    # can_back=False, can_forward=True
    ui_update_mock.assert_called_with(False, True)
    
    # 4. Go forward
    nav.forward()
    # can_back=True, can_forward=False
    ui_update_mock.assert_called_with(True, False)
