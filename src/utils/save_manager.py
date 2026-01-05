import json
import os
import time
from typing import Dict, Any, Optional
from src.utils.logger import setup_logging

logger = setup_logging()
DATA_VERSION = 1

class SaveManager:
    """
    Class for file operations (saving/loading) of game states.
    Separates I/O logic from UI logic.
    """

    @staticmethod
    def save_to_file(file_path: str, state: Dict[str, Any]) -> None:
        """Saves the state to a JSON file (atomically)."""
        data = {
            "version": DATA_VERSION,
            "state": state
        }
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        tmp_path = f"{file_path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomic replace with retry for Windows/OneDrive
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # On Windows, os.replace can fail if the file is being synced by OneDrive
                    if os.path.exists(file_path):
                        try:
                            os.replace(tmp_path, file_path)
                        except OSError:
                            # Fallback: delete and rename (not atomic, but more robust on Windows)
                            os.remove(file_path)
                            os.rename(tmp_path, file_path)
                    else:
                        os.rename(tmp_path, file_path)

                    logger.info(f"Data saved: {file_path}")
                    break
                except OSError as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(0.1) # Wait a bit and try again

        except Exception as e:
            logger.error(f"Error saving to {file_path}: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """Loads the state from a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt JSON file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading from {file_path}: {e}")
            raise

        logger.info(f"Data loaded: {file_path}")

        # Version check / migration
        if "version" in data and "state" in data:
            return data["state"]
        else:
            # Old format (direct state)
            return data
