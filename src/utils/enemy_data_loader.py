import json
import os
from typing import Dict, Any, Optional
from src.utils.logger import setup_logging
from src.config import FILES

logger = setup_logging()

class EnemyDataLoader:
    """
    Lädt und verwaltet Gegner-Presets aus JSON-Dateien.
    Singleton-ähnliches Verhalten empfohlen, um mehrfaches Laden zu vermeiden.
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
        """Lädt Gegner-Presets aus einer JSON-Datei."""

        if not os.path.exists(filepath):
            logger.warning(f"Bibliotheks-Datei nicht gefunden: {filepath}")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.enemy_presets = json.load(f)
                self.flat_presets = {}
                self._flatten_presets(self.enemy_presets)
                logger.info(f"Bibliothek geladen: {len(self.flat_presets)} Presets.")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Bibliothek: {e}")

    def _flatten_presets(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if "lp" in value: # It's a leaf (enemy)
                self.flat_presets[key] = value
            else: # It's a group
                self._flatten_presets(value)

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Gibt die Daten eines Presets zurück."""
        return self.flat_presets.get(name)

    def get_all_presets(self) -> Dict[str, Any]:
        """Gibt die hierarchischen Presets zurück."""
        return self.enemy_presets

