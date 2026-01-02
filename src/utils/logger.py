import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file: str = None) -> logging.Logger:
    # Logger konfigurieren
    logger = logging.getLogger("CombatTracker")
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # Default-Pfad berechnen, falls nicht übergeben (vermeidet Zirkelbezug zu config)
    if log_file is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "combat_tracker.log")

    # 1. Handler: Schreibt in Datei (für Fehleranalyse) - mit Rotation
    # Max 5 MB pro Datei, behalte die letzten 3 Dateien
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 2. Handler: Ausgabe in Konsole (optional)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialisiert. Log-Datei: {log_file}")
    return logger

