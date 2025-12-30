import logging
import os

def setup_logging(log_file="combat_tracker.log"):
    # Logger konfigurieren
    logger = logging.getLogger("CombatTracker")
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # 1. Handler: Schreibt in Datei (für Fehleranalyse)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
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

    logger.info("Logging initialisiert.")
    return logger

