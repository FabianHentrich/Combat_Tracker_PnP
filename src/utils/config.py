import json
import os
import platform
from typing import Dict, Tuple, Any
from src.utils.logger import setup_logging
from src.models.enums import DamageType, StatusEffectType

logger = setup_logging()

# --- THEMES ---

THEMES = {
    "Neutral Dark": {
        "bg": "#1e1e1e",       # Hintergrund (Neutral Dark Grey)
        "fg": "#d4d4d4",       # Text (Light Grey)
        "accent": "#3794ff",   # Akzent (Bright Blue)
        "panel": "#252526",    # Panel Hintergrund (Slightly Lighter Grey)
        "entry_bg": "#3c3c3c", # Eingabefelder (Medium Grey)
        "danger": "#f48771",   # Rot (Soft)
        "success": "#89d185",  # Grün (Soft)
        "warning": "#cca700",  # Gelb/Orange (Soft)
        "dead_bg": "#5e0000",
        "dead_fg": "#ffcccc",
        "low_hp_fg": "#ff5252",
        "tooltip_bg": "#252526",
        "tooltip_fg": "#d4d4d4"
    },
    "Gruvbox Dark": {
        "bg": "#282828",       # Hintergrund (Dark)
        "fg": "#ebdbb2",       # Text (Cream)
        "accent": "#83a598",   # Akzent (Blue-Green)
        "panel": "#3c3836",    # Panel
        "entry_bg": "#504945", # Entry
        "danger": "#fb4934",   # Rot
        "success": "#b8bb26",  # Grün
        "warning": "#fabd2f",  # Gelb
        "dead_bg": "#9d0006",
        "dead_fg": "#ebdbb2",
        "low_hp_fg": "#fb4934",
        "tooltip_bg": "#3c3836",
        "tooltip_fg": "#ebdbb2"
    },
    "Nord Dark": {
        "bg": "#2e3440",       # Hintergrund (Polar Night)
        "fg": "#d8dee9",       # Text (Snow Storm)
        "accent": "#88c0d0",   # Akzent (Frost Blue)
        "panel": "#3b4252",    # Panel (Lighter Polar Night)
        "entry_bg": "#4c566a", # Entry (Lightest Polar Night)
        "danger": "#bf616a",   # Rot (Aurora)
        "success": "#a3be8c",  # Grün (Aurora)
        "warning": "#ebcb8b",  # Gelb (Aurora)
        "dead_bg": "#4c566a",
        "dead_fg": "#bf616a",
        "low_hp_fg": "#d08770",
        "tooltip_bg": "#3b4252",
        "tooltip_fg": "#d8dee9"
    },
    "Monokai Dark": {
        "bg": "#272822",       # Hintergrund
        "fg": "#f8f8f2",       # Text
        "accent": "#66d9ef",   # Akzent (Cyan)
        "panel": "#3e3d32",    # Panel
        "entry_bg": "#75715e", # Entry
        "danger": "#f92672",   # Rot (Pinkish)
        "success": "#a6e22e",  # Grün
        "warning": "#fd971f",  # Orange
        "dead_bg": "#f92672",
        "dead_fg": "#f8f8f2",
        "low_hp_fg": "#fd971f",
        "tooltip_bg": "#3e3d32",
        "tooltip_fg": "#f8f8f2"
    },
    "Neutral Light": {
        "bg": "#ffffff",       # Hintergrund (White)
        "fg": "#000000",       # Text (Black) - Maximaler Kontrast
        "accent": "#007acc",   # Akzent (Blue)
        "panel": "#f3f3f3",    # Panel (Light Grey)
        "entry_bg": "#ffffff", # Entry (White)
        "danger": "#d32f2f",   # Rot
        "success": "#388e3c",  # Grün
        "warning": "#f57c00",  # Orange
        "dead_bg": "#ffebee",
        "dead_fg": "#b71c1c",
        "low_hp_fg": "#d32f2f",
        "tooltip_bg": "#ffffe0",
        "tooltip_fg": "#000000"
    },
    "Solarized Light": {
        "bg": "#fdf6e3",       # Hintergrund (Base3)
        "fg": "#073642",       # Text (Base03) - Viel dunkler als vorher
        "accent": "#268bd2",   # Akzent (Blue)
        "panel": "#eee8d5",    # Panel (Base2)
        "entry_bg": "#fdf6e3", # Entry (Base3)
        "danger": "#dc322f",   # Rot
        "success": "#859900",  # Grün
        "warning": "#b58900",  # Gelb
        "dead_bg": "#eee8d5",
        "dead_fg": "#dc322f",
        "low_hp_fg": "#cb4b16",
        "tooltip_bg": "#eee8d5",
        "tooltip_fg": "#073642"
    },
    "Gruvbox Light": {
        "bg": "#fbf1c7",       # Hintergrund (Light Cream)
        "fg": "#282828",       # Text (Dark) - Fast Schwarz
        "accent": "#458588",   # Akzent (Blue)
        "panel": "#ebdbb2",    # Panel (Beige)
        "entry_bg": "#f9f5d7", # Entry (Lighter Cream)
        "danger": "#cc241d",   # Rot
        "success": "#98971a",  # Grün
        "warning": "#d79921",  # Gelb
        "dead_bg": "#ebdbb2",
        "dead_fg": "#cc241d",
        "low_hp_fg": "#d65d0e",
        "tooltip_bg": "#ebdbb2",
        "tooltip_fg": "#282828"
    },
    "Nord Light": {
        "bg": "#eceff4",       # Hintergrund (Snow Storm)
        "fg": "#2e3440",       # Text (Polar Night) - Dunkelstes Nord-Grau
        "accent": "#5e81ac",   # Akzent (Frost Blue)
        "panel": "#e5e9f0",    # Panel
        "entry_bg": "#d8dee9", # Entry (White) -
        "danger": "#bf616a",   # Rot
        "success": "#a3be8c",  # Grün
        "warning": "#ebcb8b",  # Gelb
        "dead_bg": "#e5e9f0",
        "dead_fg": "#bf616a",
        "low_hp_fg": "#d08770",
        "tooltip_bg": "#e5e9f0",
        "tooltip_fg": "#2e3440"
    }
}

# Wähle hier das aktive Theme: "Neutral Dark", "Gruvbox Dark", "Nord Dark", "Monokai Dark", "Neutral Light", "Solarized Light"
ACTIVE_THEME = "Nord Dark"

COLORS: Dict[str, str] = THEMES[ACTIVE_THEME]

# --- KONFIGURATION ---
APP_TITLE = "PnP Combat Tracker v2.1 - Beta"

DICE_TYPES = [4, 6, 8, 10, 12, 20, 100]

GEW_TO_DICE = {
    1: 4,
    2: 6,
    3: 8,
    4: 10,
    5: 12,
    6: 20
}

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
    "log": (MONO_FONT, 9)
}

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SAVES_DIR = os.path.join(ROOT_DIR, "saves")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SAVES_DIR, exist_ok=True)

FILES = {
    "rules": os.path.join(DATA_DIR, "rules.json"),
    "hotkeys": os.path.join(DATA_DIR, "hotkeys.json"),
    "enemies": os.path.join(DATA_DIR, "enemies.json"),
    "autosave": os.path.join(SAVES_DIR, "autosave.json")
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
    # Default Full Rules Structure
    default_rules = {
      "damage_types": {
        DamageType.NORMAL.value: {
          "description": "Waffenschaden.\nSchild (SP) und Rüstung (RP) reduzieren den Schaden.",
          "ignores_armor": False,
          "ignores_shield": False
        },
        DamageType.PIERCING.value: {
          "description": "Ignoriert Rüstung (RP).\nSchild (SP) reduziert den Schaden weiterhin.",
          "ignores_armor": True,
          "ignores_shield": False
        },
        DamageType.DIRECT.value: {
          "description": "Ignoriert Rüstung (RP) und Schild (SP).\nGeht direkt auf die Lebenspunkte (LP).",
          "ignores_armor": True,
          "ignores_shield": True
        },
        DamageType.DECAY.value: {
          "description": "Verursacht Schaden und den Status 'Erosion'.",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Erosion"
        },
        DamageType.POISON.value: {
          "description": "Kann Vergiftung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Vergiftung"
        },
        DamageType.FIRE.value: {
          "description": "Kann Verbrennung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Verbrennung"
        },
        DamageType.LIGHTNING.value: {
          "description": "Kann Betäubung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Betäubung"
        },
        DamageType.COLD.value: {
          "description": "Kann Unterkühlung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Unterkühlung"
        }
      },
      "status_effects": {
        StatusEffectType.POISON.value: {
          "description": "Direktschaden (Rang) pro Runde.",
          "max_rank": 5,
          "stackable": True
        },
        StatusEffectType.BURN.value: {
          "description": "Schaden (Rang) pro Runde.",
          "max_rank": 5,
          "stackable": True
        },
        StatusEffectType.BLEED.value: {
          "description": "Schaden (Rang/2) pro Runde.\nSchaden steigt jede Runde um +1.",
          "max_rank": 5,
          "stackable": True
        },
        StatusEffectType.FREEZE.value: {
          "description": "Verlust der Bonusaktion für (Rang) Runden.",
          "max_rank": 5,
          "stackable": False
        },
        StatusEffectType.EXHAUSTION.value: {
          "description": "-2 Malus auf GEWANDTHEIT für 1 Runde.",
          "max_rank": 1,
          "stackable": False
        },
        StatusEffectType.STUN.value: {
          "description": "Ziel verliert für eine Runde alle Aktionen.",
          "max_rank": 1,
          "stackable": False
        },
        StatusEffectType.EROSION.value: {
          "description": "Dauerhafter Verlust von RANG * 1W4 Lebenspunkten (LP).",
          "max_rank": 5,
          "stackable": True
        },
        StatusEffectType.CONFUSION.value: {
          "description": "-1 Malus auf KAMPF-Probe.",
          "max_rank": 1,
          "stackable": False
        },
        StatusEffectType.BLIND.value: {
          "description": "Malus auf Aktionen/Angriffe je nach Rang (1-5).",
          "max_rank": 5,
          "stackable": False
        }
      }
    }

    # Helper to extract descriptions
    def extract_descriptions(rules_data: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        dmg_desc = {k: v.get("description", "") for k, v in rules_data.get("damage_types", {}).items()}
        status_desc = {k: v.get("description", "") for k, v in rules_data.get("status_effects", {}).items()}
        return dmg_desc, status_desc

    default_damage_desc, default_status_desc = extract_descriptions(default_rules)

    if not os.path.exists(filepath):
        return default_rules, default_damage_desc, default_status_desc

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
                return default_rules, data.get("damage_descriptions", default_damage_desc), data.get("status_descriptions", default_status_desc)

    except Exception as e:
        logger.error(f"Fehler beim Laden der Regeln: {e}")
        return default_rules, default_damage_desc, default_status_desc

def load_hotkeys(filepath: str = FILES["hotkeys"]) -> Dict[str, str]:
    default_hotkeys = {
        "next_turn": "<space>",
        "undo": "<Control-z>",
        "redo": "<Control-y>",
        "delete_char": "<Delete>",
        "focus_damage": "<Control-d>"
    }

    if not os.path.exists(filepath):
        return default_hotkeys

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_hotkeys = json.load(f)

            # Warnung bei fehlenden Keys
            missing = [k for k in default_hotkeys if k not in loaded_hotkeys]
            if missing:
                logger.warning(f"Hotkeys unvollständig. Nutze Standards für: {', '.join(missing)}")

            # Merge with defaults to ensure all keys exist
            merged_hotkeys = default_hotkeys.copy()
            merged_hotkeys.update(loaded_hotkeys)
            logger.info(f"Hotkeys geladen: {filepath}")
            return merged_hotkeys
    except Exception as e:
        logger.error(f"Fehler beim Laden der Hotkeys: {e}")
        return default_hotkeys

RULES, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS = load_rules()
HOTKEYS = load_hotkeys()
