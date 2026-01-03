import pytest
import sys
import importlib
from unittest.mock import MagicMock
from src.config import COLORS

# We need to import these inside the test or reload them to ensure they use the mocked tkinter
# But we can't easily reload inside the test function if we want to use them as types.
# So we will reload them in a fixture.

@pytest.fixture
def reloaded_modules(mock_tkinter):
    """Reloads modules to ensure they use the mocked tkinter."""
    # Patch Scrollbar to be a MagicMock so it has .set()
    mock_scrollbar_class = MagicMock()
    mock_scrollbar_instance = MagicMock()
    mock_scrollbar_class.return_value = mock_scrollbar_instance
    mock_tkinter.ttk.Scrollbar = mock_scrollbar_class

    import src.ui.components.combat.bottom_panel
    import src.ui.main_view
    import src.ui.components.dice_roller

    importlib.reload(src.ui.components.dice_roller)
    importlib.reload(src.ui.components.combat.bottom_panel)
    importlib.reload(src.ui.main_view)

    return src.ui.components.combat.bottom_panel, src.ui.main_view

@pytest.fixture
def mock_tk_root(mock_tkinter):
    """Returns a mock root widget."""
    return mock_tkinter.Tk()

@pytest.fixture
def mock_controller():
    controller = MagicMock()
    controller.combat_handler = MagicMock()
    controller.history_manager = MagicMock()
    return controller

def test_log_readonly_behavior(mock_tk_root, mock_controller, reloaded_modules):
    BottomPanelModule, MainViewModule = reloaded_modules
    BottomPanel = BottomPanelModule.BottomPanel
    MainView = MainViewModule.MainView

    # 1. Test initial state
    panel = BottomPanel(mock_tk_root, mock_controller, COLORS)

    # The log attribute is the Text widget
    log_widget = panel.log

    # 2. Test logging via MainView
    view = MainView(mock_controller, mock_tk_root)
    view.bottom_panel = panel

    message = "Test Message"
    view.log_message(message)

    # Verify sequence of calls on the log widget
    log_widget.config.assert_any_call(state="normal")
    log_widget.insert.assert_called()
    log_widget.see.assert_called()
    log_widget.config.assert_any_call(state="disabled")

    # Verify that the last config call was state="disabled"
    # Note: call_args_list contains (args, kwargs) tuples
    assert log_widget.config.call_args_list[-1][1]['state'] == 'disabled'
