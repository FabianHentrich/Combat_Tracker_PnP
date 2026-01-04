import json
import os
from typing import Dict, Any
from src.utils.logger import setup_logging

logger = setup_logging()

class RuleManager:
    """
    Lädt und verwaltet die Spielregeln aus einer externen JSON-Datei.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RuleManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, rules_path: str = "data/rules.json"):
        if not hasattr(self, 'initialized'):  # Verhindert Re-Initialisierung
            self.rules_path = rules_path
            self.rules: Dict[str, Any] = {}
            self.load_rules()
            self.initialized = True

    def load_rules(self) -> None:
        """Lädt die Regeln aus der JSON-Datei."""
        if not os.path.exists(self.rules_path):
            logger.error(f"Regel-Datei nicht gefunden: {self.rules_path}")
            # Fallback auf leeres Dict, um Abstürze zu vermeiden
            self.rules = {"damage_types": {}, "status_effects": {}}
            return

        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
            logger.info(f"Regeln erfolgreich aus {self.rules_path} geladen.")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Fehler beim Laden der Regel-Datei: {e}")
            self.rules = {"damage_types": {}, "status_effects": {}}

    def get_rules(self) -> Dict[str, Any]:
        """Gibt die geladenen Regeln zurück."""
        return self.rules

# Singleton-Instanz, die im gesamten Projekt importiert werden kann
rule_manager = RuleManager()

def get_rules() -> Dict[str, Any]:
    """Bequemlichkeitsfunktion für den Zugriff auf die Regeln."""
    return rule_manager.get_rules()
