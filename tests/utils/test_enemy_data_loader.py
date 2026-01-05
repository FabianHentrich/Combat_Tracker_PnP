import pytest
from unittest.mock import patch, mock_open
import json
from src.utils.enemy_data_loader import EnemyDataLoader

@pytest.fixture
def reset_singleton():
    """Fixture to reset the singleton instance before each test."""
    # Ensure each test gets a fresh instance
    EnemyDataLoader._instance = None

@pytest.fixture
def loader(reset_singleton):
    """Provides a clean EnemyDataLoader instance for each test."""
    # Patch __init__ to prevent automatic load_presets on instantiation
    with patch.object(EnemyDataLoader, '__init__', lambda x: None):
        loader = EnemyDataLoader()
        loader.enemy_presets = {}
        loader.flat_presets = {}
    return loader

# --- _flatten_presets Tests ---

def test_flatten_presets(loader):
    """Tests the recursive flattening of the preset dictionary."""
    nested_data = {
        "Goblins": {
            "Goblin": {"lp": 10},
            "Hobgoblin": {"lp": 15}
        },
        "Undead": {
            "Skeleton": {"lp": 20},
            "Deeper": {
                "Zombie": {"lp": 25}
            }
        }
    }
    
    loader._flatten_presets(nested_data)
    
    assert len(loader.flat_presets) == 4
    assert "Goblin" in loader.flat_presets
    assert "Skeleton" in loader.flat_presets
    assert "Zombie" in loader.flat_presets
    assert loader.flat_presets["Hobgoblin"]["lp"] == 15

# --- load_presets Tests ---

def test_load_presets_success(loader):
    """Tests the successful loading and flattening of a JSON file."""
    mock_data = {
        "Goblins": {"Goblin": {"lp": 10}}
    }
    mock_json = json.dumps(mock_data)
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_json)):
        
        loader.load_presets("dummy/path.json")
        
        assert loader.enemy_presets == mock_data
        assert "Goblin" in loader.flat_presets
        assert loader.flat_presets["Goblin"]["lp"] == 10

def test_load_presets_file_not_found(loader):
    """Tests that the loader handles a missing file gracefully."""
    with patch('os.path.exists', return_value=False):
        loader.load_presets("non_existent.json")
        
        # Presets should remain empty, and no error should be raised
        assert loader.enemy_presets == {}
        assert loader.flat_presets == {}

@patch('src.utils.enemy_data_loader.logger.error')
def test_load_presets_bad_json(mock_logger, loader):
    """Tests that the loader handles a corrupt JSON file."""
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="this is not json")):
        
        loader.load_presets("bad.json")
        
        # Presets should be empty
        assert loader.enemy_presets == {}
        assert loader.flat_presets == {}
        # An error should be logged
        mock_logger.assert_called_once()

# --- Getter Tests ---

def test_get_preset(loader):
    """Tests retrieving a single preset."""
    loader.flat_presets = {"Goblin": {"lp": 10}}
    
    preset = loader.get_preset("Goblin")
    assert preset is not None
    assert preset["lp"] == 10
    
    assert loader.get_preset("NonExistent") is None

def test_get_all_presets(loader):
    """Tests retrieving the full hierarchical preset data."""
    loader.enemy_presets = {"Goblins": {"Goblin": {"lp": 10}}}
    
    all_presets = loader.get_all_presets()
    assert all_presets == {"Goblins": {"Goblin": {"lp": 10}}}
