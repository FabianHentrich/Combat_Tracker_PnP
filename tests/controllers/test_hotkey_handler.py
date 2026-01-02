import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# sys.path.append removed. Run tests with python -m pytest

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

import src.controllers.hotkey_handler
import importlib
importlib.reload(src.controllers.hotkey_handler)
from src.controllers.hotkey_handler import HotkeyHandler

def test_safe_execute_no_focus():
    """Test: Callback wird ausgeführt, wenn kein Entry Fokus hat."""
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(root, colors)

    # Mock focus_get to return None (or something that is not an Entry)
    root.focus_get.return_value = MockWidget() # Generic widget, not Entry

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "space"

    handler.safe_execute(event, callback)

    assert callback.called

def test_safe_execute_with_focus_space():
    """Test: Callback wird NICHT ausgeführt, wenn Entry Fokus hat und Taste Space ist."""
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(root, colors)

    # Mock focus_get to return an Entry
    root.focus_get.return_value = MockEntry()

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "space"

    handler.safe_execute(event, callback)

    assert not callback.called

def test_safe_execute_with_focus_other_key():
    """Test: Callback wird ausgeführt, wenn Entry Fokus hat aber Taste NICHT Space ist."""
    root = MagicMock()
    colors = {}

    handler = HotkeyHandler(root, colors)

    root.focus_get.return_value = MockEntry()

    callback = MagicMock()
    event = MagicMock()
    event.keysym = "F5"

    handler.safe_execute(event, callback)

    assert callback.called

