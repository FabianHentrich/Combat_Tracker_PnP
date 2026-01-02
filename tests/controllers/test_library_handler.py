import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os
import tkinter as tk

# Mock tkinter globally BEFORE importing controllers
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

# Reload modules to ensure mocks are used
import importlib
import src.controllers.library_handler
import src.controllers.library_import_tab
import src.controllers.library_markdown_tab
importlib.reload(src.controllers.library_handler)
importlib.reload(src.controllers.library_import_tab)
importlib.reload(src.controllers.library_markdown_tab)

from src.controllers.library_handler import LibraryHandler
from src.controllers.library_import_tab import LibraryImportTab
from src.controllers.library_markdown_tab import LibraryMarkdownTab

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_history():
    return MagicMock()

@pytest.fixture
def mock_root():
    return MagicMock()

@pytest.fixture
def colors():
    return {"bg": "black", "panel": "gray", "fg": "white", "accent": "blue"}

def test_library_handler_init(mock_engine, mock_history, mock_root, colors):
    handler = LibraryHandler(mock_engine, mock_history, mock_root, colors)
    assert handler.engine == mock_engine
    assert handler.history_manager == mock_history
    assert handler.root == mock_root
    assert handler.colors == colors
    assert handler.markdown_tabs == {}

def test_open_library_window(mock_engine, mock_history, mock_root, colors):
    handler = LibraryHandler(mock_engine, mock_history, mock_root, colors)

    with patch('src.controllers.library_handler.tk.Toplevel') as mock_toplevel, \
         patch('src.controllers.library_handler.ttk.Notebook') as mock_notebook, \
         patch('src.controllers.library_handler.LibraryImportTab') as mock_import_tab_cls, \
         patch('src.controllers.library_handler.LibraryMarkdownTab') as mock_markdown_tab_cls:

        handler.open_library_window()

        assert mock_toplevel.called
        assert mock_notebook.called
        assert mock_import_tab_cls.called
        assert mock_markdown_tab_cls.called
        assert len(handler.markdown_tabs) > 0

def test_import_tab_filter_logic(mock_root, mock_engine, mock_history, colors):
    parent = MagicMock()

    with patch('src.controllers.library_import_tab.EnemyDataLoader') as MockLoader:
        mock_loader_instance = MockLoader.return_value
        mock_loader_instance.get_all_presets.return_value = {}
        mock_loader_instance.flat_presets = {}

        tab = LibraryImportTab(parent, mock_engine, mock_history, colors, lambda: None)

        data = {
            "Gruppe A": {
                "Gegner 1": {"lp": 10},
                "Gegner 2": {"lp": 20}
            },
            "Gruppe B": {
                "Boss": {"lp": 100}
            }
        }

        # Test 1: Suche nach "Boss"
        filtered = tab._filter_data_recursive(data, "boss")
        assert "Gruppe B" in filtered
        assert "Boss" in filtered["Gruppe B"]
        assert "Gruppe A" not in filtered

        # Test 2: Suche nach "Gegner"
        filtered = tab._filter_data_recursive(data, "gegner")
        assert "Gruppe A" in filtered
        assert "Gegner 1" in filtered["Gruppe A"]
        assert "Gegner 2" in filtered["Gruppe A"]
        assert "Gruppe B" not in filtered

        # Test 3: Suche ohne Treffer
        filtered = tab._filter_data_recursive(data, "xyz")
        assert len(filtered) == 0

def test_import_tab_add_to_staging(mock_root, mock_engine, mock_history, colors):
    parent = MagicMock()

    with patch('src.controllers.library_import_tab.EnemyDataLoader') as MockLoader, \
         patch('src.controllers.library_import_tab.ttk') as mock_ttk:

        mock_loader_instance = MockLoader.return_value
        mock_loader_instance.get_all_presets.return_value = {}
        mock_loader_instance.flat_presets = {}

        tab = LibraryImportTab(parent, mock_engine, mock_history, colors, lambda: None)
        tab.flat_presets = {"Goblin": {"lp": 7, "type": "Gegner"}}

        # Mock tree selection
        tab.tree = MagicMock()
        tab.tree.selection.return_value = ["item1"]

        def mock_tree_item(item, option):
            if option == "text": return "Goblin"
            if option == "tags": return ("enemy",)
            return None

        tab.tree.item.side_effect = mock_tree_item

        # Mock add_staging_row to verify it's called
        tab.add_staging_row = MagicMock()

        tab.add_selected_to_staging()

        # Verify that add_staging_row was called
        tab.add_staging_row.assert_called_once()
        args, _ = tab.add_staging_row.call_args
        assert args[0] == "Goblin"
        assert args[1] == {"lp": 7, "type": "Gegner"}

def test_markdown_tab_select_file(mock_root, colors):
    notebook = MagicMock()

    with patch('src.controllers.library_markdown_tab.MarkdownBrowser') as MockBrowser:
        tab = LibraryMarkdownTab(notebook, "test_tab", "Test", "dummy/path", colors, lambda x: None)

        # Test select_file delegation
        tab.select_file("path/to/FileA.md")

        tab.browser.select_file.assert_called_once_with("path/to/FileA.md")



def test_global_search_switching(mock_engine, mock_history, mock_root, colors):
    """
    Testet, ob die globale Suche korrekt den Tab wechselt, wenn im aktuellen Tab nichts gefunden wird.
    """
    handler = LibraryHandler(mock_engine, mock_history, mock_root, colors)

    # Mock UI components
    handler.notebook = MagicMock()
    handler.global_search_var = MagicMock()
    handler.global_search_var.get.return_value = "test"

    # Mock Import Tab
    mock_import_tab = MagicMock()
    mock_import_tab.parent = "import_frame"
    mock_import_tab.search.return_value = 0 # No results in import tab
    handler.import_tab = mock_import_tab

    # Mock Markdown Tabs
    mock_tab1 = MagicMock()
    mock_tab1.frame = "tab1_frame"
    mock_tab1.search.return_value = 0 # No results

    mock_tab2 = MagicMock()
    mock_tab2.frame = "tab2_frame"
    mock_tab2.search.return_value = 5 # 5 results found here!

    handler.markdown_tabs = {
        "tab1": mock_tab1,
        "tab2": mock_tab2
    }

    # Setup notebook tabs order
    handler.notebook.tabs.return_value = ["import_frame", "tab1_frame", "tab2_frame"]

    # Setup nametowidget to return the string itself (simulating widget path match)
    # In the real code we compare str(widget) == tab_id.
    # Here we mock nametowidget to return an object whose str() is the tab_id
    def mock_nametowidget(name):
        widget = MagicMock()
        widget.__str__.return_value = name
        return widget

    # Actually, in the fixed code we compare str(controller.frame) == tab_id
    # So we need controller.frame to be convertible to string matching tab_id
    mock_import_tab.parent = MagicMock()
    mock_import_tab.parent.__str__.return_value = "import_frame"

    mock_tab1.frame = MagicMock()
    mock_tab1.frame.__str__.return_value = "tab1_frame"

    mock_tab2.frame = MagicMock()
    mock_tab2.frame.__str__.return_value = "tab2_frame"

    handler.notebook.nametowidget.side_effect = mock_nametowidget

    # Case 1: Current tab is "import_frame" (no results), should switch to "tab2_frame"
    handler.notebook.select.return_value = "import_frame"

    handler._on_global_search()

    # Verify search was called on all controllers
    mock_import_tab.search.assert_called_with("test")
    mock_tab1.search.assert_called_with("test")
    mock_tab2.search.assert_called_with("test")

    # Verify switch to tab2_frame
    handler.notebook.select.assert_called_with("tab2_frame")

    # Case 2: Current tab is "tab2_frame" (has results), should NOT switch
    handler.notebook.select.reset_mock()
    handler.notebook.select.return_value = "tab2_frame"

    handler._on_global_search()

    # Should not call select with a new tab (only called to get current tab)
    # We can check if it was called with an argument
    calls = [c for c in handler.notebook.select.call_args_list if c.args]
    assert len(calls) == 0

def test_library_navigation(mock_engine, mock_history, mock_root, colors):
    """
    Testet die Navigations-Historie (Vor/Zurück) in der Bibliothek.
    """
    handler = LibraryHandler(mock_engine, mock_history, mock_root, colors)

    # Mock UI components
    handler.btn_back = MagicMock()
    handler.btn_forward = MagicMock()
    handler.notebook = MagicMock()

    # Mock Tabs
    mock_tab1 = MagicMock()
    mock_tab1.frame = MagicMock()
    mock_tab1.frame.__str__.return_value = "tab1_frame"

    mock_tab2 = MagicMock()
    mock_tab2.frame = MagicMock()
    mock_tab2.frame.__str__.return_value = "tab2_frame"

    handler.markdown_tabs = {
        "tab1": mock_tab1,
        "tab2": mock_tab2
    }

    # Setup notebook tabs
    handler.notebook.tabs.return_value = ["tab1_frame", "tab2_frame"]

    def mock_nametowidget(name):
        if name == "tab1_frame": return mock_tab1.frame
        if name == "tab2_frame": return mock_tab2.frame
        return MagicMock()
    handler.notebook.nametowidget.side_effect = mock_nametowidget

    # 1. Initial state
    assert len(handler.navigator.history) == 0
    assert handler.navigator.index == -1

    # 2. Navigate to Tab 1
    handler.on_navigation_event("tab1", "file1.md")
    assert len(handler.navigator.history) == 1
    assert handler.navigator.index == 0
    assert handler.navigator.history[0] == {'tab_id': 'tab1', 'filepath': 'file1.md'}
    handler.btn_back.config.assert_called_with(state="disabled")
    handler.btn_forward.config.assert_called_with(state="disabled")

    # 3. Navigate to Tab 2
    handler.on_navigation_event("tab2", "file2.md")
    assert len(handler.navigator.history) == 2
    assert handler.navigator.index == 1
    handler.btn_back.config.assert_called_with(state="normal")
    handler.btn_forward.config.assert_called_with(state="disabled")

    # 4. Go Back
    handler.go_back()
    assert handler.navigator.index == 0
    # Should restore Tab 1
    # Check if notebook.select was called with index of tab1 (0)
    handler.notebook.select.assert_called_with(0)
    # Check if display_content was called
    mock_tab1.display_content.assert_called_with("file1.md")

    handler.btn_back.config.assert_called_with(state="disabled")
    handler.btn_forward.config.assert_called_with(state="normal")

    # 5. Go Forward
    handler.go_forward()
    assert handler.navigator.index == 1
    # Should restore Tab 2
    handler.notebook.select.assert_called_with(1)
    mock_tab2.display_content.assert_called_with("file2.md")

    handler.btn_back.config.assert_called_with(state="normal")
    handler.btn_forward.config.assert_called_with(state="disabled")

    # 6. Navigate to new page from middle of history (truncation)
    handler.go_back() # Index 0
    handler.on_navigation_event("tab1", "file3.md")

    assert len(handler.navigator.history) == 2 # Old forward history (Tab 2) should be gone
    assert handler.navigator.index == 1
    assert handler.navigator.history[1] == {'tab_id': 'tab1', 'filepath': 'file3.md'}

    handler.btn_back.config.assert_called_with(state="normal")
    handler.btn_forward.config.assert_called_with(state="disabled")
