import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocke tkinter Module
# Wir definieren Dummy-Klassen, damit isinstance funktioniert
class MockWidget:
    pass

class MockEntry(MockWidget):
    pass

class MockText(MockWidget):
    pass

# Erstelle ein Mock-Modul für tkinter.ttk
mock_ttk = MagicMock()
mock_ttk.Entry = MockEntry
sys.modules['tkinter.ttk'] = mock_ttk

# Erstelle ein Mock-Modul für tkinter
mock_tk = MagicMock()
mock_tk.Entry = MockEntry
mock_tk.Text = MockText
mock_tk.ttk = mock_ttk # WICHTIG: ttk muss auch als Attribut verfügbar sein
sys.modules['tkinter'] = mock_tk

sys.modules['tkinter.messagebox'] = MagicMock()

import src.hotkey_handler
import importlib
importlib.reload(src.hotkey_handler)
from src.hotkey_handler import HotkeyHandler

def test_safe_execute_no_focus():
    """Test: Callback wird ausgeführt, wenn kein Entry Fokus hat."""
    tracker = MagicMock()
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(tracker, root, colors)

    # Mock focus_get to return None (or something that is not an Entry)
    root.focus_get.return_value = MockWidget() # Generic widget, not Entry

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "space"

    handler.safe_execute(event, callback)

    assert callback.called

def test_safe_execute_with_focus_space():
    """Test: Callback wird NICHT ausgeführt, wenn Entry Fokus hat und Taste Space ist."""
    tracker = MagicMock()
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(tracker, root, colors)

    # Mock focus_get to return an Entry
    root.focus_get.return_value = MockEntry()

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "space"

    handler.safe_execute(event, callback)

    assert not callback.called

def test_safe_execute_with_focus_other_key():
    """Test: Callback wird ausgeführt, wenn Entry Fokus hat aber Taste NICHT Space ist."""
    tracker = MagicMock()
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(tracker, root, colors)

    root.focus_get.return_value = MockEntry()

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "F5"

    handler.safe_execute(event, callback)

    assert callback.called

