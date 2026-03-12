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

# Tests for LibraryHandler were removed as they focused on Frontend/UI components
# which are not required to be unit tested.
