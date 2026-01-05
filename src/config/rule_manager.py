import json
import os
from typing import Dict, Any
from src.utils.logger import setup_logging
from src.utils.localization import localization_manager
from src.models.enums import RuleKey

logger = setup_logging()

class RuleManager:
    """
    Loads and manages the game rules from an external, language-specific JSON file.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RuleManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.rules: Dict[str, Any] = {}
            self.load_rules()
            self.initialized = True

    def load_rules(self) -> None:
        """Loads the rules from the JSON file based on the current language."""
        language_code = localization_manager.language_code
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rules_path = os.path.join(base_dir, '..', 'data', 'i18n', f'{language_code}_rules.json')

        if not os.path.exists(rules_path):
            logger.error(f"Rules file not found: {rules_path}")
            # Fallback to empty dict to avoid crashes
            self.rules = {RuleKey.DAMAGE_TYPES.value: {}, RuleKey.STATUS_EFFECTS.value: {}}
            return

        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
            logger.info(f"Rules successfully loaded from {rules_path}.")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading rules file: {e}")
            self.rules = {RuleKey.DAMAGE_TYPES.value: {}, RuleKey.STATUS_EFFECTS.value: {}}

    def get_rules(self) -> Dict[str, Any]:
        """Returns the loaded rules."""
        return self.rules

    @property
    def damage_type_descriptions(self) -> Dict[str, str]:
        """Dynamically gets descriptions for damage types from current rules."""
        return {k: v.get(RuleKey.DESCRIPTION.value, "") for k, v in self.rules.get(RuleKey.DAMAGE_TYPES.value, {}).items()}

    @property
    def status_effect_descriptions(self) -> Dict[str, str]:
        """Dynamically gets descriptions for status effects from current rules."""
        return {k: v.get(RuleKey.DESCRIPTION.value, "") for k, v in self.rules.get(RuleKey.STATUS_EFFECTS.value, {}).items()}

# Singleton instance that can be imported throughout the project
rule_manager = RuleManager()

def get_rules() -> Dict[str, Any]:
    """Convenience function for accessing the rules."""
    return rule_manager.get_rules()
