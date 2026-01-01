import pytest
from unittest.mock import MagicMock, patch
import sys
from tests.mocks import MockWidget, MockVar, MockTreeview, MockScrollableFrame

# Pre-import modules that might be used in tests to avoid reloading warnings
# when sys.modules is patched.
try:
    import numpy
except ImportError:
    pass

try:
    import openpyxl
except ImportError:
    pass

# --- Fixtures ---

@pytest.fixture(scope="function")
def mock_tkinter():
    """Mocks tkinter and ttk modules."""
    mock_tk_module = MagicMock()
    mock_tk_module.Tk = MockWidget
    mock_tk_module.Toplevel = MockWidget
    mock_tk_module.Canvas = MockWidget
    mock_tk_module.Frame = MockWidget
    mock_tk_module.LabelFrame = MockWidget
    mock_tk_module.Label = MockWidget
    mock_tk_module.Button = MockWidget
    mock_tk_module.Checkbutton = MockWidget
    mock_tk_module.Spinbox = MockWidget
    mock_tk_module.Scrollbar = MockWidget
    mock_tk_module.BooleanVar = MockVar
    mock_tk_module.StringVar = MockVar
    mock_tk_module.IntVar = MockVar
    mock_tk_module.DoubleVar = MockVar

    mock_ttk_module = MagicMock()
    mock_ttk_module.Frame = MockWidget
    mock_ttk_module.LabelFrame = MockWidget
    mock_ttk_module.Label = MockWidget
    mock_ttk_module.Button = MockWidget
    mock_ttk_module.Checkbutton = MockWidget
    mock_ttk_module.Spinbox = MockWidget
    mock_ttk_module.Scrollbar = MockWidget
    mock_ttk_module.Treeview = MockTreeview

    # Link ttk to tk module
    mock_tk_module.ttk = mock_ttk_module

    with patch.dict(sys.modules, {
        'tkinter': mock_tk_module,
        'tkinter.ttk': mock_ttk_module,
        'tkinter.filedialog': MagicMock(),
        'tkinter.simpledialog': MagicMock(),
        'tkinter.messagebox': MagicMock()
    }):
        yield mock_tk_module

@pytest.fixture(scope="function")
def mock_pygame():
    """Mocks pygame module."""
    mock_pg = MagicMock()
    mock_pg.mixer = MagicMock()
    mock_pg.mixer.music = MagicMock()
    mock_pg.event = MagicMock()

    with patch.dict(sys.modules, {
        'pygame': mock_pg,
        'pygame.mixer': mock_pg.mixer,
        'pygame.mixer.music': mock_pg.mixer.music,
        'pygame.event': mock_pg.event,
        'mutagen': MagicMock()
    }):
        yield mock_pg
