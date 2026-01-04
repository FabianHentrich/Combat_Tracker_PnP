import pytest
from unittest.mock import patch, mock_open
import json
from src.config.rule_manager import RuleManager

# Beispiel-JSON-Daten für die Tests
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
    Setzt die Singleton-Instanz des RuleManagers vor jedem Test in dieser Datei zurück.
    Dies ist entscheidend, um sicherzustellen, dass jeder Test mit einer sauberen,
    neuen Instanz beginnt und nicht durch den globalen Zustand beeinflusst wird.
    """
    RuleManager._instance = None
    yield
    RuleManager._instance = None


def test_load_rules_success():
    """
    Testet das erfolgreiche Laden von Regeln aus einer gültigen JSON-Datei.
    """
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=MOCK_RULES_JSON)):
            # Durch das Fixture wird hier eine NEUE Instanz erstellt
            manager = RuleManager(rules_path="dummy.json")
            rules = manager.get_rules()
            
            assert "TestDmg" in rules["damage_types"]
            assert rules["damage_types"]["TestDmg"]["ignores_armor"] is True
            assert "TestStatus" in rules["status_effects"]

def test_load_rules_file_not_found():
    """
    Testet das Verhalten, wenn die Regel-Datei nicht existiert.
    Es sollten leere, aber gültige Regel-Strukturen zurückgegeben werden.
    """
    with patch("os.path.exists", return_value=False):
        manager = RuleManager(rules_path="nonexistent.json")
        rules = manager.get_rules()
        
        assert "damage_types" in rules
        assert "status_effects" in rules
        assert not rules["damage_types"]  # Dictionary sollte leer sein
        assert not rules["status_effects"] # Dictionary sollte leer sein

def test_load_rules_json_error():
    """
    Testet das Verhalten bei einer fehlerhaften JSON-Datei.
    Sollte ebenfalls auf eine leere, sichere Struktur zurückfallen.
    """
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            manager = RuleManager(rules_path="bad.json")
            rules = manager.get_rules()

            assert "damage_types" in rules
            assert "status_effects" in rules
            assert not rules["damage_types"]
            assert not rules["status_effects"]

def test_singleton_behavior():
    """
    Stellt sicher, dass der RuleManager ein Singleton ist.
    """
    # Dieser Test funktioniert jetzt zuverlässig, da die Instanz vorher zurückgesetzt wurde.
    manager1 = RuleManager()
    manager2 = RuleManager()
    
    assert manager1 is manager2
