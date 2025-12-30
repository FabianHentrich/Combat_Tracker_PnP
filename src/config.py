import json
import os
from typing import Dict, Tuple, Any
from .logger import setup_logging

logger = setup_logging()

# Farben für das Dark Theme
COLORS: Dict[str, str] = {
    "bg": "#1a1b26",       # Tiefes Nachtblau
    "fg": "#a9b1d6",       # Weiches Grau-Blau
    "accent": "#656bb6",   # Helles Blau
    "panel": "#24283b",    # Panel Hintergrund
    "entry_bg": "#414868", # Eingabefelder
    "danger": "#f7768e",   # Rot
    "success": "#9ece6a",  # Grün
    "warning": "#e0af68"   # Orange/Gelb
}

def load_rules(filepath: str = "rules.json") -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, str]]:
    # Default Full Rules Structure
    default_rules = {
      "damage_types": {
        "Normal": {
          "description": "Waffenschaden.\nSchild (SP) und Rüstung (RP) reduzieren den Schaden.",
          "ignores_armor": False,
          "ignores_shield": False
        },
        "Durchschlagend": {
          "description": "Ignoriert Rüstung (RP).\nSchild (SP) reduziert den Schaden weiterhin.",
          "ignores_armor": True,
          "ignores_shield": False
        },
        "Direkt": {
          "description": "Ignoriert Rüstung (RP) und Schild (SP).\nGeht direkt auf die Lebenspunkte (LP).",
          "ignores_armor": True,
          "ignores_shield": True
        },
        "Verwesung": {
          "description": "Verursacht Schaden und den Status 'Erosion'.",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Erosion"
        },
        "Gift": {
          "description": "Kann Vergiftung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Vergiftung"
        },
        "Feuer": {
          "description": "Kann Verbrennung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Verbrennung"
        },
        "Blitz": {
          "description": "Kann Betäubung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Betäubung"
        },
        "Kälte": {
          "description": "Kann Unterkühlung verursachen (Chance abhängig vom Rang).",
          "ignores_armor": False,
          "ignores_shield": False,
          "secondary_effect": "Unterkühlung"
        }
      },
      "status_effects": {
        "Vergiftung": {
          "description": "Direktschaden (Rang) pro Runde.",
          "max_rank": 6,
          "stackable": True
        },
        "Verbrennung": {
          "description": "Schaden (Rang) pro Runde.",
          "max_rank": 6,
          "stackable": True
        },
        "Blutung": {
          "description": "Schaden (Rang/2) pro Runde.\nSchaden steigt jede Runde um +1.",
          "max_rank": 6,
          "stackable": True
        },
        "Unterkühlung": {
          "description": "Verlust der Bonusaktion für (Rang) Runden.",
          "max_rank": 6,
          "stackable": False
        },
        "Erschöpfung": {
          "description": "-2 Malus auf GEWANDTHEIT für 1 Runde.",
          "max_rank": 1,
          "stackable": False
        },
        "Betäubung": {
          "description": "Ziel verliert für eine Runde alle Aktionen.",
          "max_rank": 1,
          "stackable": False
        },
        "Erosion": {
          "description": "Dauerhafter Verlust von RANG * 1W4 Lebenspunkten (LP).",
          "max_rank": 6,
          "stackable": True
        },
        "Verwirrung": {
          "description": "-1 Malus auf KAMPF-Probe.",
          "max_rank": 1,
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
                return data, dmg_desc, status_desc
            else:
                # Old structure fallback (unlikely to be used if we control the file, but safe)
                return default_rules, data.get("damage_descriptions", default_damage_desc), data.get("status_descriptions", default_status_desc)

    except Exception as e:
        logger.error(f"Fehler beim Laden der Regeln: {e}")
        return default_rules, default_damage_desc, default_status_desc

def load_hotkeys(filepath: str = "hotkeys.json") -> Dict[str, str]:
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
            return json.load(f)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Hotkeys: {e}")
        return default_hotkeys

RULES, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS = load_rules()
HOTKEYS = load_hotkeys()
