import pytest
from unittest.mock import patch, mock_open
import json
from src.utils.localization import Localization
from src.models.enums import Language

@pytest.fixture
def manager():
    """Provides a Localization instance with mocked file loading."""
    with patch.object(Localization, 'load_translations'):
        manager = Localization(Language.ENGLISH.value)
        manager.translations = {} # Ensure it's clean for each test
        yield manager

# --- get() Tests ---

def test_get_simple_key(manager):
    """Tests retrieving a simple, non-nested translation."""
    manager.translations = {"greeting": "Hello"}
    assert manager.get("greeting") == "Hello"

def test_get_nested_key(manager):
    """Tests retrieving a value using dot notation."""
    manager.translations = {"dialog": {"title": {"confirm": "Confirmation"}}}
    assert manager.get("dialog.title.confirm") == "Confirmation"

def test_get_with_kwargs_formatting(manager):
    """Tests placeholder replacement."""
    manager.translations = {"welcome": "Hello, {name}!"}
    assert manager.get("welcome", name="World") == "Hello, World!"

def test_get_fallback_on_missing_key(manager):
    """Tests that the key itself is returned if not found."""
    manager.translations = {}
    assert manager.get("non.existent.key") == "non.existent.key"

def test_get_fallback_on_missing_placeholder(manager):
    """Tests that the unformatted string is returned if a placeholder is missing."""
    manager.translations = {"greeting": "Hello, {name}!"}
    # Missing the 'name' kwarg
    assert manager.get("greeting") == "Hello, {name}!"

# --- load_translations() and set_language() Tests ---

@patch('os.path.exists', return_value=True)
def test_load_translations_success(mock_exists):
    """Tests successful loading of a JSON file."""
    mock_data = {"greeting": "Hallo"}
    mock_json = json.dumps(mock_data)
    
    with patch('builtins.open', mock_open(read_data=mock_json)):
        manager = Localization(Language.GERMAN.value)
        assert manager.translations == mock_data

@patch('os.path.exists', side_effect=[False, True]) # Fails for 'de', succeeds for 'en'
def test_load_translations_fallback_to_english(mock_exists):
    """Tests that it falls back to English if the language file is not found."""
    mock_data_en = {"greeting": "Hello"}
    mock_json_en = json.dumps(mock_data_en)
    
    with patch('builtins.open', mock_open(read_data=mock_json_en)) as mock_file:
        manager = Localization(Language.GERMAN.value)
        
        # It should have tried to open the German file first, then the English one
        assert mock_file.call_count == 2
        assert 'de.json' in mock_file.call_args_list[0][0][0]
        assert 'en.json' in mock_file.call_args_list[1][0][0]
        
        # The final translations should be the English ones
        assert manager.language_code == Language.ENGLISH.value
        assert manager.translations == mock_data_en

@patch('os.path.exists', return_value=True)
@patch('json.load', side_effect=json.JSONDecodeError("Syntax error", "", 0))
def test_load_translations_bad_json(mock_json_load, mock_exists):
    """Tests that it handles a corrupt JSON file gracefully."""
    with patch('builtins.open', mock_open(read_data="bad json")):
        manager = Localization(Language.ENGLISH.value)
        # Translations should be empty, and it should not crash
        assert manager.translations == {}

def test_set_language_reloads_translations(manager):
    """Tests that set_language triggers a reload."""
    with patch.object(manager, 'load_translations') as mock_load:
        manager.set_language(Language.GERMAN.value)
        assert manager.language_code == Language.GERMAN.value
        mock_load.assert_called_once()
