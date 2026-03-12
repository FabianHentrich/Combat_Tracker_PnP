import pytest
from unittest.mock import patch, mock_open
import json
from src.config.rule_manager import RuleManager

# Example JSON data for the tests
MOCK_RULES_JSON = json.dumps({
    "damage_types": {
        "TestDmg": {"description": "Test", "ignores_armor": True}
    },
    "status_effects": {
        "TestStatus": {"description": "Test", "max_rank": 1}
    }
})

@pytest.fixture(autouse=True)
def reset_rule_manager_singleton():
    """
    Resets the RuleManager singleton instance before each test in this file.
    This is crucial to ensure that each test starts with a clean,
    new instance and is not affected by global state.
    """
    RuleManager._instance = None
    yield
    RuleManager._instance = None

def test_load_rules_success():
    """
    Tests the successful loading of rules from a valid JSON file.
    """
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=MOCK_RULES_JSON)), \
         patch("src.config.rule_manager.localization_manager.language_code", "en"):
        
        # A NEW instance is created here due to the fixture
        manager = RuleManager()
        rules = manager.get_rules()
        
        assert "TestDmg" in rules["damage_types"]
        assert rules["damage_types"]["TestDmg"]["ignores_armor"] is True
        assert "TestStatus" in rules["status_effects"]

def test_load_rules_file_not_found():
    """
    Tests the behavior when the rule file does not exist.
    It should return empty but valid rule structures.
    """
    with patch("os.path.exists", return_value=False), \
         patch("src.config.rule_manager.localization_manager.language_code", "en"):
        
        manager = RuleManager()
        rules = manager.get_rules()
        
        assert "damage_types" in rules
        assert "status_effects" in rules
        assert not rules["damage_types"]  # Dictionary should be empty
        assert not rules["status_effects"] # Dictionary should be empty

def test_load_rules_json_error():
    """
    Tests the behavior with a faulty JSON file.
    Should also fall back to an empty, safe structure.
    """
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="invalid json")), \
         patch("src.config.rule_manager.localization_manager.language_code", "en"):
        
        manager = RuleManager()
        rules = manager.get_rules()

        assert "damage_types" in rules
        assert "status_effects" in rules
        assert not rules["damage_types"]
        assert not rules["status_effects"]

def test_singleton_behavior():
    """
    Ensures that the RuleManager is a singleton.
    """
    # This test now works reliably because the instance was reset beforehand.
    with patch("src.config.rule_manager.localization_manager.language_code", "en"):
        manager1 = RuleManager()
        manager2 = RuleManager()
    
    assert manager1 is manager2
