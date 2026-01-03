import json
import os
import time
from typing import Dict, Any, Optional
from src.utils.logger import setup_logging

logger = setup_logging()
DATA_VERSION = 1

class SaveManager:
    """
    Klasse für Datei-Operationen (Speichern/Laden) von Spielständen.
    Trennt IO-Logik von UI-Logik.
    """

    @staticmethod
    def save_to_file(file_path: str, state: Dict[str, Any]) -> None:
        """Speichert den Zustand in eine JSON-Datei (atomar)."""
        data = {
            "version": DATA_VERSION,
            "state": state
        }
        # Verzeichnis erstellen falls nicht existent
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        tmp_path = f"{file_path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomares Ersetzen (Atomic Write) mit Retry für Windows/OneDrive
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Auf Windows kann os.replace fehlschlagen, wenn die Datei gerade von OneDrive gesynct wird
                    if os.path.exists(file_path):
                        try:
                            os.replace(tmp_path, file_path)
                        except OSError:
                            # Fallback: Löschen und Umbenennen (nicht atomar, aber robuster auf Windows)
                            os.remove(file_path)
                            os.rename(tmp_path, file_path)
                    else:
                        os.rename(tmp_path, file_path)

                    logger.info(f"Daten gespeichert: {file_path}")
                    break
                except OSError as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(0.1) # Kurz warten und erneut versuchen

        except Exception as e:
            logger.error(f"Fehler beim Speichern nach {file_path}: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """Lädt den Zustand aus einer JSON-Datei."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Korrupte JSON-Datei {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Fehler beim Laden von {file_path}: {e}")
            raise

        logger.info(f"Daten geladen: {file_path}")

        # Version check / migration
        if "version" in data and "state" in data:
            return data["state"]
        else:
            # Old format (direct state)
            return data
