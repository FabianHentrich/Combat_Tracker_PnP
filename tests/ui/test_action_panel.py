import pytest
from unittest.mock import MagicMock, patch
import importlib
import src.ui.components.combat.action_panel

class DummyLabelFrame:
    """A dummy class to replace ttk.LabelFrame for testing inheritance."""
    def __init__(self, *args, **kwargs):
        pass
    def pack(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass
    def config(self, *args, **kwargs): pass
    def destroy(self): pass

# Mock tkinter before import
# We replace LabelFrame with a real class so ActionPanel inherits from a real class, not a Mock.
# This allows patch.object to work correctly on ActionPanel methods.
@patch('tkinter.ttk.LabelFrame', new=DummyLabelFrame)
@patch('tkinter.StringVar')
def get_action_panel(MockStringVar):
    # Reload the module to ensure ActionPanel inherits from the patched LabelFrame (DummyLabelFrame)
    importlib.reload(src.ui.components.combat.action_panel)
    from src.ui.components.combat.action_panel import ActionPanel
    
    # Mock controller and its handlers
    mock_controller = MagicMock()
    mock_controller.combat_handler = MagicMock()
    mock_controller.character_handler = MagicMock()
    
    # Mock UI creation
    # Now that ActionPanel is a real class (inheriting from DummyLabelFrame), we can patch _setup_ui safely.
    with patch.object(ActionPanel, '_setup_ui', autospec=True):
        panel = ActionPanel(parent=MagicMock(), controller=mock_controller, colors={})

        # Manually mock UI elements that the get_* methods depend on
        panel.damage_rows = []
        panel.status_rank = MagicMock()
        panel.status_duration = MagicMock()
        panel.status_combobox = MagicMock()
        panel.management_target_var = MagicMock()
        
        # Mock the translated maps
        panel.translated_damage_types = {"Normal": "NORMAL"}
        panel.translated_status_effects = {"Poison": "POISON"}
        panel.translated_scopes = {"Selected": "SELECTED"}

    return panel

@pytest.fixture
def panel():
    """Provides an ActionPanel instance with mocked UI elements."""
    return get_action_panel()

def _add_mock_damage_row(panel, amount_str, type_str):
    """Helper to add a mocked damage row to the panel."""
    row = {
        "amount": MagicMock(),
        "type": MagicMock()
    }
    row["amount"].get.return_value = amount_str
    row["type"].get.return_value = type_str
    panel.damage_rows.append(row)

# --- Data Getter Method Tests ---

def test_calculate_total_and_get_value(panel):
    """Tests the total calculation with valid and invalid inputs."""
    _add_mock_damage_row(panel, "10", "Normal")
    _add_mock_damage_row(panel, "5", "Fire")
    _add_mock_damage_row(panel, "abc", "Invalid") # Should be ignored
    
    # Mock the label that displays the total
    panel.lbl_total = MagicMock()
    
    total = panel.calculate_total()
    assert total == 15
    panel.lbl_total.config.assert_called_with(text="Total: 15")
    
    # get_value should return the same
    assert panel.get_value() == 15

def test_get_damage_data(panel):
    """Tests the aggregation of damage data and detail string creation."""
    _add_mock_damage_row(panel, "10", "Normal")
    _add_mock_damage_row(panel, "5", "Fire")
    _add_mock_damage_row(panel, "0", "Cold") # Should be ignored in details
    
    panel.lbl_total = MagicMock() # Needed for calculate_total call
    
    total, details = panel.get_damage_data()
    
    assert total == 15
    assert details == "10 Normal, 5 Fire"

def test_get_damage_data_no_damage(panel):
    """Tests the fallback for get_damage_data when total damage is zero."""
    _add_mock_damage_row(panel, "0", "Normal")
    panel.lbl_total = MagicMock()
    
    total, details = panel.get_damage_data()
    
    assert total == 0
    assert details == "0 Normal"

def test_get_status_input(panel):
    """Tests that status input is read and converted correctly."""
    panel.status_combobox.get.return_value = "Poison"
    panel.status_rank.get.return_value = "2"
    panel.status_duration.get.return_value = "5"
    
    status_input = panel.get_status_input()
    
    assert status_input["status"] == "POISON"
    assert status_input["rank"] == 2
    assert status_input["duration"] == 5

def test_get_status_input_invalid(panel):
    """Tests the fallback for invalid (non-numeric) rank/duration."""
    panel.status_combobox.get.return_value = "Poison"
    panel.status_rank.get.return_value = "abc"
    panel.status_duration.get.return_value = "xyz"
    
    status_input = panel.get_status_input()
    
    assert status_input["rank"] == 1 # Default
    assert status_input["duration"] == 3 # Default

def test_get_management_target(panel):
    """Tests the conversion of the management target selection."""
    panel.management_target_var.get.return_value = "Selected"
    
    target = panel.get_management_target()
    
    assert target == "SELECTED"
