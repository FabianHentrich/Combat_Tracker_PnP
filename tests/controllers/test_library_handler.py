# noinspection PyPackageRequirements
import pytest
from unittest.mock import MagicMock, patch, call
import sys
import importlib

# Ensure we have the real tkinter module available for specs.
# If it's a mock (leaked from another test), we remove it and re-import.
if 'tkinter' in sys.modules and (hasattr(sys.modules['tkinter'], 'assert_called') or hasattr(sys.modules['tkinter'], 'reset_mock')):
    del sys.modules['tkinter']

import tkinter as tk
import src.controllers.library_handler
import src.controllers.library_markdown_tab
import src.utils.navigation_manager
import src.config

@pytest.fixture
def mock_deps():
    """Provides common mocked dependencies for the handler."""
    # Double check inside fixture in case it got mocked again between import and fixture execution
    global tk
    if 'tkinter' in sys.modules and (
            hasattr(sys.modules['tkinter'], 'assert_called') or hasattr(sys.modules['tkinter'], 'reset_mock')):
        del sys.modules['tkinter']
        import tkinter
        tk = tkinter

    root = MagicMock(spec=tk.Tk)
    engine = MagicMock()
    history_manager = MagicMock()
    colors = {"bg": "#FFF", "fg": "#000"}
    return root, engine, history_manager, colors

@pytest.fixture
def handler(mock_deps):
    """
    Provides a LibraryHandler instance with a fully mocked UI structure.
    Reloads the controller module to prevent mock leakage from other tests.
    """
    # Ensure a clean slate for the modules under test
    importlib.reload(src.config)
    importlib.reload(src.utils.navigation_manager)
    importlib.reload(src.controllers.library_handler)
    importlib.reload(src.controllers.library_markdown_tab)
    
    root, engine, history_manager, colors = mock_deps
    
    # Patch all required UI components to isolate the test.
    # We patch the tk alias directly in the module to ensure it uses our mocks.
    # Note: ttk is imported as 'from tkinter import ttk', so we patch it directly in the module namespace.
    with patch('src.controllers.library_handler.tk.Toplevel'), \
         patch('src.controllers.library_handler.ttk.Notebook'), \
         patch('src.controllers.library_handler.ttk.Button') as mock_button_cls, \
         patch('src.controllers.library_handler.ttk.Frame'), \
         patch('src.controllers.library_handler.ttk.Label'), \
         patch('src.controllers.library_handler.ttk.Entry'), \
         patch('src.controllers.library_handler.tk.StringVar'), \
         patch('src.controllers.library_handler.LibraryImportTab') as MockImportTab, \
         patch('src.controllers.library_handler.LibraryMarkdownTab') as MockMarkdownTab:

        # Configure ttk.Button to return a NEW mock on each call.
        # This ensures btn_back and btn_forward are distinct objects.
        mock_button_cls.side_effect = lambda *args, **kwargs: MagicMock()

        # Instantiate the handler using the reloaded module
        h = src.controllers.library_handler.LibraryHandler(root, engine, history_manager, colors)
        
        h.data_manager = MagicMock()
        h.open_library_window()

        # Simulate one markdown tab for testing purposes
        mock_rules_tab = MockMarkdownTab.return_value
        mock_rules_tab.search.return_value = 0
        mock_rules_tab.frame = MagicMock()
        mock_rules_tab.search_var = MagicMock()
        h.markdown_tabs = {"rules": mock_rules_tab}

        # Configure the import tab mock
        h.import_tab = MockImportTab.return_value
        h.import_tab.parent = MagicMock() # Mock the parent frame

        # Configure the notebook mock
        h.notebook.tabs.return_value = ["import_tab_frame", "rules_tab_frame"]
        h.notebook.nametowidget.side_effect = lambda name: {
            "import_tab_frame": h.import_tab.parent,
            "rules_tab_frame": mock_rules_tab.frame
        }.get(name)
        
        yield h

# --- Tests ---

def test_open_library_window_builds_ui(handler):
    """Tests that opening the window correctly initializes UI components."""
    assert handler.lib_window is not None
    assert handler.notebook is not None
    assert handler.global_search_var is not None
    handler.notebook.add.assert_called()

def test_search_and_open_direct_hit(handler):
    """Tests that a direct file hit correctly selects the tab and displays content."""
    handler.data_manager.search_file.return_value = ("rules", "/mock/rules/combat.md")
    rules_tab = handler.markdown_tabs["rules"]
    
    handler.search_and_open("Combat")
    
    handler.notebook.select.assert_called_with(1)
    rules_tab.display_content.assert_called_with("/mock/rules/combat.md")
    rules_tab.select_file.assert_called_with("/mock/rules/combat.md")

def test_search_and_open_no_direct_hit(handler):
    """Tests that a global search is triggered if no direct file match is found."""
    handler.data_manager.search_file.return_value = None
    
    with patch.object(handler, '_on_global_search') as mock_global_search:
        handler.search_and_open("Unknown")
        mock_global_search.assert_called_once()

def test_on_global_search_delegates_to_tabs(handler):
    """Tests that a global search calls the search method on all tab controllers."""
    rules_tab = handler.markdown_tabs["rules"]
    rules_tab.search.return_value = 1
    
    # Configure the import tab mock to return an integer for search
    handler.import_tab.search.return_value = 0
    
    handler.global_search_var.get.return_value = "test query"
    
    def get_controller(widget_id):
        if widget_id == "import_tab_frame": return handler.import_tab
        if widget_id == "rules_tab_frame": return rules_tab
        return None
        
    with patch.object(handler, '_get_controller_by_widget_id', side_effect=get_controller):
        handler._on_global_search()

    handler.import_tab.search.assert_called_with("test query")
    rules_tab.search.assert_called_with("test query")

def test_library_navigation_flow(handler):
    """Tests the back/forward navigation history flow."""
    rules_tab = handler.markdown_tabs["rules"]
    
    # Ensure MAX_HISTORY is large enough to allow back navigation
    with patch('src.utils.navigation_manager.MAX_HISTORY', 10):
        handler.on_navigation_event("rules", "file1.md")
        handler.on_navigation_event("rules", "file2.md")

    assert handler.navigator.index == 1
    
    # Check that config was called twice (once for each push)
    # 1. First push: Back disabled
    # 2. Second push: Back enabled
    assert handler.btn_back.config.call_count == 2
    
    # Verify the sequence of calls
    handler.btn_back.config.assert_has_calls([
        call(state="disabled"),
        call(state="normal")
    ])

    # Patch logger to catch swallowed exceptions in _restore_state
    with patch('src.controllers.library_handler.logger.error') as mock_error:
        handler.navigator.back()
        if mock_error.called:
            pytest.fail(f"Logger error called: {mock_error.call_args}")

    assert handler.navigator.index == 0
    handler.notebook.select.assert_called_with(1)
    rules_tab.display_content.assert_called_with("file1.md")
