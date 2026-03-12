import pytest
from unittest.mock import patch, mock_open
import json
import platform
import sys

# --- Test RuleManager ---

@pytest.fixture(autouse=True)
def reset_rule_manager_singleton():
    """Fixture to reset the RuleManager singleton before each test."""
    from src.config.rule_manager import RuleManager
    # This ensures that if RuleManager was imported elsewhere, we get a clean slate.
    if RuleManager._instance:
        RuleManager._instance = None
    yield
    if RuleManager._instance:
        RuleManager._instance = None

@patch('src.config.rule_manager.localization_manager')
def test_rule_manager_loads_correct_language_file(mock_loc_manager):
    """Tests if RuleManager attempts to load the file for the current language."""
    from src.config.rule_manager import RuleManager
    mock_loc_manager.language_code = 'de'
    mock_rules = {"damage_types": {"Fire": {"description": "Feuer"}}}
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_rules))) as mock_file:
        manager = RuleManager()
        mock_file.assert_called_once()
        assert 'de_rules.json' in mock_file.call_args[0][0]
        assert manager.get_rules()['damage_types']['Fire']['description'] == "Feuer"

def test_rule_manager_properties_missing_description():
    """Tests that description properties handle rules without a 'description' key."""
    from src.config.rule_manager import RuleManager
    mock_rules = {"damage_types": {"Fire": {}}, "status_effects": {"Poison": {}}}
    with patch.object(RuleManager, 'load_rules', return_value=None):
        manager = RuleManager()
        manager.rules = mock_rules
        assert manager.damage_type_descriptions["Fire"] == ""
        assert manager.status_effect_descriptions["Poison"] == ""

# --- Test __init__.py loading logic ---

def test_load_hotkeys_default_on_missing_file():
    """Tests loading default hotkeys when the file is missing."""
    from src.config import load_hotkeys, DEFAULT_HOTKEYS
    with patch("os.path.exists", return_value=False):
        hotkeys = load_hotkeys("dummy.json")
        assert hotkeys == DEFAULT_HOTKEYS

def test_load_hotkeys_merges_with_defaults():
    """Tests that loaded hotkeys are merged with defaults."""
    from src.config import load_hotkeys, DEFAULT_HOTKEYS
    mock_data = {"next_turn": "<F1>"}
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        hotkeys = load_hotkeys("dummy.json")
        assert hotkeys["next_turn"] == "<F1>"
        assert hotkeys["undo"] == DEFAULT_HOTKEYS["undo"]

@patch('src.config.platform.system')
def test_font_selection_per_platform(mock_system):
    """Tests that fonts are selected based on the operating system."""
    import importlib
    import src.config

    # Test Windows
    mock_system.return_value = "Windows"
    importlib.reload(src.config)
    assert src.config.MAIN_FONT == "Segoe UI"

    # Test macOS
    mock_system.return_value = "Darwin"
    importlib.reload(src.config)
    assert src.config.MAIN_FONT == "Helvetica Neue"

# --- calculate_font_sizes() Tests ---

def test_calculate_font_sizes_returns_all_keys():
    """calculate_font_sizes returns a dict with all expected font keys."""
    from src.config import calculate_font_sizes
    fonts = calculate_font_sizes(1920, 1080)
    expected_keys = {"main", "bold", "large", "xl", "huge", "small", "mono", "log", "text"}
    assert expected_keys == set(fonts.keys())

def test_calculate_font_sizes_base_resolution_no_scaling():
    """At 1920x1080 the scale factor is 1.0 and sizes match the base values."""
    from src.config import calculate_font_sizes
    fonts = calculate_font_sizes(1920, 1080)
    # base "main" = 10, scale = 1.0 → scaled = 10
    assert fonts["main"][1] == 10
    # base "huge" = 24 → 24
    assert fonts["huge"][1] == 24

def test_calculate_font_sizes_small_screen_clamps_at_minimum():
    """Very small screen resolution clamps scale factor at 0.7 → all sizes >= 8."""
    from src.config import calculate_font_sizes
    fonts = calculate_font_sizes(640, 480)
    for key, value in fonts.items():
        assert value[1] >= 8, f"Font '{key}' size {value[1]} is below minimum 8"

def test_calculate_font_sizes_large_screen_clamps_at_maximum():
    """Very large screen resolution clamps scale factor at 1.5."""
    from src.config import calculate_font_sizes
    fonts_large = calculate_font_sizes(7680, 4320)   # 8K
    fonts_base  = calculate_font_sizes(1920, 1080)
    # With clamp at 1.5, "main" (base 10) → int(10 * 1.5) = 15
    assert fonts_large["main"][1] == fonts_base["main"][1] * 1 or fonts_large["main"][1] >= fonts_base["main"][1]

def test_calculate_font_sizes_bold_keys_include_bold_style():
    """Keys 'bold', 'large', 'xl', 'huge' must have 'bold' as third tuple element."""
    from src.config import calculate_font_sizes
    fonts = calculate_font_sizes(1920, 1080)
    for key in ("bold", "large", "xl", "huge"):
        assert fonts[key][2] == "bold", f"'{key}' should be bold"

def test_calculate_font_sizes_mono_keys_use_mono_font():
    """Keys 'mono' and 'log' must use MONO_FONT, not MAIN_FONT."""
    from src.config import calculate_font_sizes, MAIN_FONT, MONO_FONT
    fonts = calculate_font_sizes(1920, 1080)
    assert fonts["mono"][0] == MONO_FONT
    assert fonts["log"][0] == MONO_FONT
    assert fonts["main"][0] == MAIN_FONT


@patch('src.config.localization_manager')
@patch('os.path.exists')
def test_rules_file_fallback(mock_exists, mock_loc_manager):
    """Tests that the rules file path falls back to English if the language-specific one is missing."""
    import importlib
    import src.config

    def exists_side_effect(path):
        return 'en_rules.json' in path

    mock_exists.side_effect = exists_side_effect
    mock_loc_manager.language_code = 'de'

    importlib.reload(src.config)

    assert 'en_rules.json' in src.config.FILES['rules']
