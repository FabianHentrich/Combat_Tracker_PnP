import pytest
from unittest.mock import MagicMock, patch

# Mock tkinter before import
@patch('tkinter.ttk.LabelFrame')
def get_quick_add_panel(MockLabelFrame):
    from src.ui.components.combat.quick_add_panel import QuickAddPanel
    
    mock_controller = MagicMock()
    
    with patch.object(QuickAddPanel, '_setup_ui'):
        panel = QuickAddPanel(parent=MagicMock(), controller=mock_controller)
        
        # Manually mock all the UI elements the methods interact with
        panel.entry_name = MagicMock()
        panel.entry_lp = MagicMock()
        panel.entry_rp = MagicMock()
        panel.entry_sp = MagicMock()
        panel.entry_init = MagicMock()
        panel.entry_gew = MagicMock()
        panel.entry_level = MagicMock()
        panel.entry_type = MagicMock()
        panel.var_surprise = MagicMock()
        
        # Mock the translated map used by get_data
        panel.translated_types = {"Player": "PLAYER", "Enemy": "ENEMY"}
        
    return panel

@pytest.fixture
def panel():
    """Provides a QuickAddPanel instance with mocked UI elements."""
    return get_quick_add_panel()

# --- get_data Test ---

def test_get_data(panel):
    """Tests that data is correctly retrieved from the UI elements."""
    # Assign return values to the mocked UI elements
    panel.entry_name.get.return_value = "Test Character"
    panel.entry_lp.get.return_value = "50"
    panel.entry_rp.get.return_value = "5"
    panel.entry_sp.get.return_value = "0"
    panel.entry_init.get.return_value = "12"
    panel.entry_gew.get.return_value = "3"
    panel.entry_level.get.return_value = "2"
    panel.entry_type.get.return_value = "Player" # The display value
    panel.var_surprise.get.return_value = True
    
    data = panel.get_data()
    
    assert data["name"] == "Test Character"
    assert data["lp"] == "50"
    assert data["init"] == "12"
    assert data["type"] == "PLAYER" # Check that the value was correctly translated
    assert data["surprise"] is True

# --- UI Manipulation Tests ---

def test_clear(panel):
    """Tests that the clear method calls delete() on all relevant entries."""
    panel.clear()
    
    panel.entry_name.delete.assert_called_once_with(0, 'end')
    panel.entry_lp.delete.assert_called_once_with(0, 'end')
    panel.entry_rp.delete.assert_called_once_with(0, 'end')
    panel.entry_sp.delete.assert_called_once_with(0, 'end')
    panel.entry_init.delete.assert_called_once_with(0, 'end')
    panel.entry_gew.delete.assert_called_once_with(0, 'end')
    panel.entry_level.delete.assert_called_once_with(0, 'end')
    
    panel.entry_name.focus.assert_called_once()
    panel.var_surprise.set.assert_called_once_with(False)

def test_set_defaults(panel):
    """Tests that default values are set correctly."""
    with patch('src.ui.components.combat.quick_add_panel.DEFAULT_GEW', 1):
        panel.set_defaults()
    
    panel.var_surprise.set.assert_called_once_with(False)
    panel.entry_gew.delete.assert_called_once_with(0, 'end')
    panel.entry_gew.insert.assert_called_once_with(0, "1")
    panel.entry_level.delete.assert_called_once_with(0, 'end')
    panel.entry_level.insert.assert_called_once_with(0, "0")

def test_fill_fields(panel):
    """Tests that the fill_fields method correctly populates the UI."""
    data = {
        "name": "Loaded Char",
        "lp": 88,
        "rp": 7,
        "sp": 5,
        "gew": 4,
        "init": 18,
        "level": 5,
        "type": "ENEMY"
    }
    
    # Mock the reverse translation for setting the combobox
    with patch('src.ui.components.combat.quick_add_panel.translate', return_value="Enemy"):
        panel.fill_fields(data)
    
    panel.entry_name.insert.assert_called_with(0, "Loaded Char")
    panel.entry_lp.insert.assert_called_with(0, "88")
    panel.entry_rp.insert.assert_called_with(0, "7")
    panel.entry_sp.insert.assert_called_with(0, "5")
    panel.entry_gew.insert.assert_called_with(0, "4")
    panel.entry_init.insert.assert_called_with(0, "18")
    panel.entry_level.insert.assert_called_with(0, "5")
    panel.entry_type.set.assert_called_with("Enemy")
