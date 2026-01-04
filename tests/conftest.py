import pytest
from unittest.mock import MagicMock, patch
import sys
from tests.mocks import MockWidget, MockVar, MockTreeview, MockScrollableFrame
from src.models.enums import DamageType, StatusEffectType

# Pre-import modules that might be used in tests to avoid reloading warnings
# when sys.modules is patched.
try:
    import numpy
except ImportError:
    pass

try:
    import openpyxl
except ImportError:
    pass

# --- Mock Data ---

MOCK_RULES = {
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


# --- Fixtures ---

@pytest.fixture(autouse=True)
def mock_rules(monkeypatch):
    """
    Monkeypatches the get_rules function to return a consistent mock rule set
    for all tests, isolating them from the external rules.json file.
    """
    # Patch the function in the modules where it is *used*.
    monkeypatch.setattr('src.core.mechanics.get_rules', lambda: MOCK_RULES)
    monkeypatch.setattr('src.models.character.get_rules', lambda: MOCK_RULES)
    # Add more modules here if they also import and use get_rules.
    # For example:
    # monkeypatch.setattr('src.ui.some_component.get_rules', lambda: MOCK_RULES)


@pytest.fixture(scope="function")
def mock_tkinter():
    """Mocks tkinter and ttk modules."""
    mock_tk_module = MagicMock()
    mock_tk_module.Tk = MockWidget
    mock_tk_module.Toplevel = MockWidget
    mock_tk_module.Canvas = MockWidget
    mock_tk_module.Frame = MockWidget
    mock_tk_module.LabelFrame = MockWidget
    mock_tk_module.Label = MockWidget
    mock_tk_module.Button = MockWidget
    mock_tk_module.Checkbutton = MockWidget
    mock_tk_module.Spinbox = MockWidget
    mock_tk_module.Scrollbar = MockWidget
    mock_tk_module.BooleanVar = MockVar
    mock_tk_module.StringVar = MockVar
    mock_tk_module.IntVar = MockVar
    mock_tk_module.DoubleVar = MockVar

    mock_ttk_module = MagicMock()
    mock_ttk_module.Frame = MockWidget
    mock_ttk_module.LabelFrame = MockWidget
    mock_ttk_module.Label = MockWidget
    mock_ttk_module.Button = MockWidget
    mock_ttk_module.Checkbutton = MockWidget
    mock_ttk_module.Spinbox = MockWidget
    mock_ttk_module.Scrollbar = MockWidget
    mock_ttk_module.Treeview = MockTreeview

    # Link ttk to tk module
    mock_tk_module.ttk = mock_ttk_module

    with patch.dict(sys.modules, {
        'tkinter': mock_tk_module,
        'tkinter.ttk': mock_ttk_module,
        'tkinter.filedialog': MagicMock(),
        'tkinter.simpledialog': MagicMock(),
        'tkinter.messagebox': MagicMock()
    }):
        yield mock_tk_module

@pytest.fixture(scope="function")
def mock_pygame():
    """Mocks pygame module."""
    mock_pg = MagicMock()
    mock_pg.mixer = MagicMock()
    mock_pg.mixer.music = MagicMock()
    mock_pg.event = MagicMock()

    with patch.dict(sys.modules, {
        'pygame': mock_pg,
        'pygame.mixer': mock_pg.mixer,
        'pygame.mixer.music': mock_pg.mixer.music,
        'pygame.event': mock_pg.event,
        'mutagen': MagicMock()
    }):
        yield mock_pg
