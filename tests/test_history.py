import pytest
from unittest.mock import MagicMock
import sys
import os

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocke tkinter Module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from src.engine import CombatEngine
from src.character import Character
from src.history import HistoryManager

@pytest.fixture
def engine():
    return CombatEngine()

@pytest.fixture
def history(engine):
    return HistoryManager(engine)

def test_history_snapshot_and_undo(engine, history):
    """
    Testet das Erstellen eines Snapshots und das Rückgängigmachen (Undo).
    Überprüft, ob der Zustand vor der Änderung wiederhergestellt wird.
    """
    c = Character("Hero", 100, 10, 5, 20)
    engine.add_character(c)

    # Initial state
    assert engine.characters[0].lp == 100

    # Save snapshot
    history.save_snapshot()

    # Modify state
    engine.characters[0].lp = 50
    assert engine.characters[0].lp == 50

    # Undo
    success = history.undo()
    assert success is True
    assert engine.characters[0].lp == 100

def test_history_redo(engine, history):
    """
    Testet das Wiederherstellen einer rückgängig gemachten Aktion (Redo).
    Überprüft, ob der Zustand nach der Änderung wiederhergestellt wird.
    """
    c = Character("Hero", 100, 10, 5, 20)
    engine.add_character(c)

    history.save_snapshot()
    engine.characters[0].lp = 50

    history.undo()
    assert engine.characters[0].lp == 100

    # Redo
    success = history.redo()
    assert success is True
    assert engine.characters[0].lp == 50

def test_history_stack_limit(engine, history):
    """
    Testet das Limit des Undo-Stacks.
    Überprüft, ob ältere Snapshots entfernt werden, wenn das Limit erreicht ist.
    """
    history.max_history = 2

    c = Character("Hero", 100, 10, 5, 20)
    engine.add_character(c)

    # 1. Snapshot (LP 100)
    history.save_snapshot()
    engine.characters[0].lp = 90

    # 2. Snapshot (LP 90)
    history.save_snapshot()
    engine.characters[0].lp = 80

    # 3. Snapshot (LP 80) - Should push out the first one (LP 100)
    history.save_snapshot()
    engine.characters[0].lp = 70

    assert len(history.undo_stack) == 2

    # Undo 1 -> LP 80
    history.undo()
    assert engine.characters[0].lp == 80

    # Undo 2 -> LP 90
    history.undo()
    assert engine.characters[0].lp == 90

    # Undo 3 -> Should fail (stack empty)
    success = history.undo()
    assert success is False
    assert engine.characters[0].lp == 90

def test_redo_cleared_on_new_action(engine, history):
    """
    Testet, ob der Redo-Stack geleert wird, wenn eine neue Aktion ausgeführt wird.
    """
    c = Character("Hero", 100, 10, 5, 20)
    engine.add_character(c)

    history.save_snapshot()
    engine.characters[0].lp = 90

    history.undo()
    assert engine.characters[0].lp == 100
    assert len(history.redo_stack) == 1

    # New action clears redo stack
    history.save_snapshot()
    engine.characters[0].lp = 50

    assert len(history.redo_stack) == 0
    assert history.redo() is False

