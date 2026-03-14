import json
import os
import platform
from typing import Dict, Tuple, Any
from src.utils.logger import setup_logging
from src.models.enums import Language
from .defaults import THEMES, DICE_TYPES, GEW_TO_DICE, DEFAULT_HOTKEYS, LIBRARY_TABS
from .rule_manager import get_rules, rule_manager
from src.utils.localization import localization_manager

logger = setup_logging()

# --- LANGUAGE ---
AVAILABLE_LANGUAGES = [lang.value for lang in Language]

# Choose the active theme here: "Neutral Dark", "Gruvbox Dark", "Nord Dark", "Monokai Dark", "Neutral Light", "Solarized Light"
ACTIVE_THEME = "Nord Dark"

COLORS: Dict[str, str] = THEMES[ACTIVE_THEME]

# --- CONFIGURATION ---
APP_TITLE = "PnP Combat Tracker v2.1 - Beta"

# Platform-dependent fonts
system = platform.system()
if system == "Windows":
    MAIN_FONT = "Segoe UI"
    MONO_FONT = "Consolas"
elif system == "Darwin":  # macOS
    MAIN_FONT = "Helvetica Neue"
    MONO_FONT = "Menlo"
else:  # Linux and others
    MAIN_FONT = "DejaVu Sans" # Often available, otherwise fallback
    MONO_FONT = "DejaVu Sans Mono"

def calculate_font_sizes(screen_width: int = 1920, screen_height: int = 1080) -> Dict[str, Tuple]:
    """
    Calculates font sizes dynamically based on screen resolution.
    Base sizes are optimized for 1920x1080 displays.
    """
    # Calculate scaling factor based on screen dimensions
    # Use geometric mean for balanced scaling
    base_width, base_height = 1920, 1080
    width_scale = screen_width / base_width
    height_scale = screen_height / base_height
    scale_factor = (width_scale * height_scale) ** 0.5

    # Clamp scale factor to reasonable bounds
    scale_factor = max(0.7, min(scale_factor, 1.5))

    # Base font sizes for 1920x1080
    base_sizes = {
        "main": 10,
        "bold": 10,
        "large": 12,
        "xl": 14,
        "huge": 24,
        "small": 9,
        "mono": 9,
        "log": 9,
        "text": 11
    }

    fonts = {}
    for key, base_size in base_sizes.items():
        scaled_size = max(8, int(base_size * scale_factor))
        if key == "bold":
            fonts[key] = (MAIN_FONT, scaled_size, "bold")
        elif key == "large":
            fonts[key] = (MAIN_FONT, scaled_size, "bold")
        elif key == "xl":
            fonts[key] = (MAIN_FONT, scaled_size, "bold")
        elif key == "huge":
            fonts[key] = (MAIN_FONT, scaled_size, "bold")
        elif key in ["mono", "log"]:
            fonts[key] = (MONO_FONT, scaled_size)
        else:
            fonts[key] = (MAIN_FONT, scaled_size)

    return fonts

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

# Construct the path to the rules file based on language
language_code = localization_manager.language_code
rules_file = os.path.join(DATA_DIR, "i18n", f"{language_code}_rules.json")
if not os.path.exists(rules_file):
    rules_file = os.path.join(DATA_DIR, "i18n", f"{Language.ENGLISH.value}_rules.json") # Fallback to English

FILES = {
    "rules": rules_file,
    "hotkeys": os.path.join(DATA_DIR, "hotkeys.json"),
    "enemies": os.path.join(DATA_DIR, "enemies.json"),
    "library_db": os.path.join(DATA_DIR, "library.db"),
    "autosave": os.path.join(SAVES_DIR, "autosave.json"),
    "lock": os.path.join(SAVES_DIR, "running.lock"),
    "log": os.path.join(LOGS_DIR, "combat_tracker.log")
}

WINDOW_SIZE = {
    "main": None,  # No fixed size, will maximize
    "main_min": (1200, 800),  # Minimum size for main window
    "library": "1200x900",
    "library_min": (800, 600),
    "import": "1200x900",
    "import_min": (800, 600),
    "edit": "450x600",
    "hotkeys": "450x600",
    "small_dialog": "300x120"
}

def load_hotkeys(filepath: str = FILES["hotkeys"]) -> Dict[str, str]:
    if not os.path.exists(filepath):
        return DEFAULT_HOTKEYS

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_hotkeys = json.load(f)

            # Warning for missing keys
            missing = [k for k in DEFAULT_HOTKEYS if k not in loaded_hotkeys]
            if missing:
                logger.warning(f"Hotkeys incomplete. Using defaults for: {', '.join(missing)}")

            # Merge with defaults to ensure all keys exist
            merged_hotkeys = DEFAULT_HOTKEYS.copy()
            merged_hotkeys.update(loaded_hotkeys)
            logger.info(f"Hotkeys loaded: {filepath}")
            return merged_hotkeys
    except Exception as e:
        logger.error(f"Error loading hotkeys: {e}")
        return DEFAULT_HOTKEYS

# Load the rules and extract the descriptions
RULES = get_rules()
# The old static dictionaries are removed.
# Descriptions are now accessed dynamically via rule_manager properties.
HOTKEYS = load_hotkeys()

# --- HISTORY ---
MAX_HISTORY = 20
