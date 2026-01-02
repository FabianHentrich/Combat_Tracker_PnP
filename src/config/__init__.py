import json
import os
import platform
from typing import Dict, Tuple, Any
from src.utils.logger import setup_logging
from src.models.enums import DamageType, StatusEffectType
from .defaults import THEMES, DEFAULT_RULES, DICE_TYPES, GEW_TO_DICE, DEFAULT_HOTKEYS

logger = setup_logging()

# Wähle hier das aktive Theme: "Neutral Dark", "Gruvbox Dark", "Nord Dark", "Monokai Dark", "Neutral Light", "Solarized Light"
ACTIVE_THEME = "Nord Dark"

COLORS: Dict[str, str] = THEMES[ACTIVE_THEME]

# --- KONFIGURATION ---
APP_TITLE = "PnP Combat Tracker v2.1 - Beta"

# Plattform-abhängige Schriftarten
system = platform.system()
if system == "Windows":
    MAIN_FONT = "Segoe UI"
    MONO_FONT = "Consolas"
elif system == "Darwin":  # macOS
    MAIN_FONT = "Helvetica Neue"
    MONO_FONT = "Menlo"
else:  # Linux und andere
    MAIN_FONT = "DejaVu Sans" # Oft verfügbar, sonst Fallback
    MONO_FONT = "DejaVu Sans Mono"

FONTS = {
    "main": (MAIN_FONT, 10),
    "bold": (MAIN_FONT, 10, "bold"),
    "large": (MAIN_FONT, 12, "bold"),
    "xl": (MAIN_FONT, 14, "bold"),
    "huge": (MAIN_FONT, 24, "bold"),
    "small": (MAIN_FONT, 9),
    "mono": (MONO_FONT, 9),
    "log": (MONO_FONT, 9),
    "text": (MAIN_FONT, 11)
}

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SAVES_DIR = os.path.join(ROOT_DIR, "saves")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SAVES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

FILES = {
    "rules": os.path.join(DATA_DIR, "rules.json"),
    "hotkeys": os.path.join(DATA_DIR, "hotkeys.json"),
    "enemies": os.path.join(DATA_DIR, "enemies.json"),
    "autosave": os.path.join(SAVES_DIR, "autosave.json"),
    "log": os.path.join(LOGS_DIR, "combat_tracker.log")
}

WINDOW_SIZE = {
    "main": "1900x1200",
    "library": "1200x900",
    "import": "1200x900",
    "edit": "450x600",
    "hotkeys": "450x600",
    "small_dialog": "300x120"
}

def load_rules(filepath: str = FILES["rules"]) -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, str]]:
    # Helper to extract descriptions
    def extract_descriptions(rules_data: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        dmg_desc = {k: v.get("description", "") for k, v in rules_data.get("damage_types", {}).items()}
        status_desc = {k: v.get("description", "") for k, v in rules_data.get("status_effects", {}).items()}
        return dmg_desc, status_desc

    default_damage_desc, default_status_desc = extract_descriptions(DEFAULT_RULES)

    if not os.path.exists(filepath):
        return DEFAULT_RULES, default_damage_desc, default_status_desc

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Check if new structure
            if "damage_types" in data and "status_effects" in data:
                dmg_desc, status_desc = extract_descriptions(data)
                logger.info(f"Regelwerk erfolgreich geladen: {filepath}")
                return data, dmg_desc, status_desc
            else:
                # Old structure fallback (unlikely to be used if we control the file, but safe)
                logger.info(f"Altes Regelwerk-Format geladen: {filepath}")
                return DEFAULT_RULES, data.get("damage_descriptions", default_damage_desc), data.get("status_descriptions", default_status_desc)

    except Exception as e:
        logger.error(f"Fehler beim Laden der Regeln: {e}")
        return DEFAULT_RULES, default_damage_desc, default_status_desc

def load_hotkeys(filepath: str = FILES["hotkeys"]) -> Dict[str, str]:
    if not os.path.exists(filepath):
        return DEFAULT_HOTKEYS

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_hotkeys = json.load(f)

            # Warnung bei fehlenden Keys
            missing = [k for k in DEFAULT_HOTKEYS if k not in loaded_hotkeys]
            if missing:
                logger.warning(f"Hotkeys unvollständig. Nutze Standards für: {', '.join(missing)}")

            # Merge with defaults to ensure all keys exist
            merged_hotkeys = DEFAULT_HOTKEYS.copy()
            merged_hotkeys.update(loaded_hotkeys)
            logger.info(f"Hotkeys geladen: {filepath}")
            return merged_hotkeys
    except Exception as e:
        logger.error(f"Fehler beim Laden der Hotkeys: {e}")
        return DEFAULT_HOTKEYS

RULES, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS = load_rules()
HOTKEYS = load_hotkeys()

# --- HISTORY ---
MAX_HISTORY = 20

