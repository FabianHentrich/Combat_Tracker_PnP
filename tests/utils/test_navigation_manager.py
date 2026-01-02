import pytest
from unittest.mock import MagicMock
from src.utils.navigation_manager import NavigationManager
from src.config import MAX_HISTORY

def test_push_and_restore():
    """Testet Hinzufügen und Wiederherstellen."""
    restore_mock = MagicMock()
    nav = NavigationManager(restore_mock)

    state1 = {"id": 1}
    state2 = {"id": 2}

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

def test_history_limit():
    """Testet, ob MAX_HISTORY eingehalten wird."""
    nav = NavigationManager(MagicMock())

    # Fülle History über Limit
    for i in range(MAX_HISTORY + 5):
        nav.push({"id": i})

    assert len(nav.history) == MAX_HISTORY
    assert nav.history[-1]["id"] == MAX_HISTORY + 4
    assert nav.history[0]["id"] == 5 # Die ersten 5 sollten rausgeflogen sein

def test_overwrite_future():
    """Testet, dass 'Zukunft' abgeschnitten wird, wenn man zurückgeht und was neues macht."""
    nav = NavigationManager(MagicMock())

    nav.push({"id": 1})
    nav.push({"id": 2})
    nav.push({"id": 3})

    nav.back() # bei id 2
    nav.back() # bei id 1

    nav.push({"id": 4}) # Neuer Pfad

    assert len(nav.history) == 2
    assert nav.history[0]["id"] == 1
    assert nav.history[1]["id"] == 4

