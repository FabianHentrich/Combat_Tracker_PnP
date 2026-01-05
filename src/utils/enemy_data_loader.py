import json
import os
from typing import Dict, Any, Optional
from src.utils.logger import setup_logging
from src.config import FILES

logger = setup_logging()

class EnemyDataLoader:
    """
    Loads and manages enemy presets from JSON files.
    Singleton-like behavior is recommended to avoid multiple loads.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnemyDataLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.enemy_presets: Dict[str, Any] = {}
        self.flat_presets: Dict[str, Any] = {}
        self._initialized = True
        self.load_presets()

    def load_presets(self, filepath: str = FILES["enemies"]) -> None:
        """Loads enemy presets from a JSON file."""

        if not os.path.exists(filepath):
            logger.warning(f"Library file not found: {filepath}")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.enemy_presets = json.load(f)
                self.flat_presets = {}
                self._flatten_presets(self.enemy_presets)
                logger.info(f"Library loaded: {len(self.flat_presets)} presets.")
        except Exception as e:
            logger.error(f"Error loading library: {e}")

    def _flatten_presets(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if "lp" in value: # It's a leaf (enemy)
                self.flat_presets[key] = value
            else: # It's a group
                self._flatten_presets(value)

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the data of a preset."""
        return self.flat_presets.get(name)

    def get_all_presets(self) -> Dict[str, Any]:
        """Returns the hierarchical presets."""
        return self.enemy_presets
