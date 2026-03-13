# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the application
python Combat_Tracker.py

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run a single test file
pytest tests/core/test_engine.py

# Run a specific test by name
pytest tests/core/test_engine.py::TestClassName::test_method_name

# Run tests with coverage
pytest --cov=src
```

---

## Architecture Overview

The app is a Tkinter-based PnP combat tracker using MVC with a pub/sub event core. There is **no dependency injection framework** — `CombatTracker.__init__` in `src/ui/main_window.py` is the explicit composition root that manually wires all components together.

```
Combat_Tracker.py          ← entry point, creates tk.Tk and CombatTracker
└── src/ui/main_window.py  ← CombatTracker: composition root
    ├── src/core/engine.py         ← CombatEngine: owns character list + delegates
    ├── src/core/turn_manager.py   ← TurnManager: rounds, initiative, status ticks
    ├── src/core/history.py        ← HistoryManager: undo/redo via state snapshots
    ├── src/core/event_manager.py  ← EventManager: pub/sub (UPDATE, LOG, TURN_CHANGE)
    ├── src/controllers/           ← one handler per concern (damage, import, audio…)
    ├── src/ui/main_view.py        ← MainView: implements ICombatView protocol
    └── src/config/__init__.py     ← COLORS, FONTS, theme, window settings
```

---

## Key Design Patterns

### 1. Every mutating action follows this pattern
```python
self.history_manager.save_snapshot()   # snapshot BEFORE the action
self.engine.do_something()             # mutate state
# engine.notify(EventType.UPDATE) fires automatically inside engine methods
```
Always call `history_manager.save_snapshot()` before any state mutation in a controller. This is what enables undo/redo.

### 2. Event flow (core → UI)
`CombatEngine` fires events via `EventManager`. UI components subscribe using:
```python
engine.subscribe(EventType.UPDATE, self.update_listbox)
engine.subscribe(EventType.LOG, self.log_message)
engine.subscribe(EventType.TURN_CHANGE, self.on_turn_change)
```
**Never let UI code directly mutate `engine.characters`.** All mutations go through `CombatEngine` or `TurnManager` methods.

### 3. `ICombatView` protocol (`src/ui/interfaces.py`)
Controllers only talk to the UI through this interface. Key methods controllers call on the view:
- `view.get_damage_data()` → `(total_dmg: int, details_str: str)`
- `view.get_status_input()` → `dict` with `rank`, `duration`, `effect`
- `view.get_selected_char_id()` → `str | None`
- `view.log_message(msg)`, `view.update_listbox()`

---

## Data Flow: Damage Calculation

```
CombatActionHandler.deal_damage()
  → reads UI via view.get_damage_data()
  → calls engine.apply_damage(char, amount, damage_type, rank, details)
      → character.apply_damage(dmg, damage_type, rank)
          → mechanics.calculate_damage(character, dmg, damage_type, rank)
              → RuleManager.get_rules()["damage_types"][damage_type]
              → applies shield → armor → HP reduction in sequence
              → returns DamageResult
      → engine fires EventType.UPDATE + EventType.LOG
```

**Damage priority chain in `src/core/mechanics.py:calculate_damage()`:**
1. **Shield (SP):** absorbs up to `character.sp` damage, 1:1
2. **Armor (RP):** absorbs up to `character.rp * 2` remaining damage; armor loses `(absorbed + 1) // 2` durability
3. **HP (LP):** remainder hits LP directly

Damage type flags (from `data/i18n/{lang}_rules.json`):
- `ignores_shield: true` → skip step 1
- `ignores_armor: true` → skip step 2
- `secondary_effect: "BURN"` → shown in log as a chance to trigger that status effect

---

## Data Flow: Status Effects

Status effects tick in `TurnManager._update_character_status()`, called at the **start of each character's turn** via `next_turn()`.

Each effect's `apply_round_effect(character)` is called, which:
- Deals damage (Poison → DIRECT, Burn → NORMAL, Bleed → NORMAL scaling with rounds)
- Modifies state (Stun sets `character.skip_turns = 1`, Erosion reduces `character.max_lp`)
- Returns a log string

**To add a new status effect:**
1. Add the name to `StatusEffectType` enum in `src/models/enums.py`
2. Create a subclass of `StatusEffect` in `src/models/status_effects.py` with `apply_round_effect()`
3. Register it in the `EFFECT_CLASSES` dict at the bottom of `src/models/status_effects.py`
4. Add its config to `data/i18n/de_rules.json` and `data/i18n/en_rules.json` under `"status_effects"`
5. Add translation strings to `data/i18n/de.json` and `data/i18n/en.json` under `"messages.status"`

---

## Where Rules & Config Live

### Game mechanics rules: `data/i18n/{lang}_rules.json`
This is the **primary place to add or change damage types and status effects** without touching Python.

Structure:
```json
{
  "damage_types": {
    "FIRE": {
      "ignores_armor": false,
      "ignores_shield": false,
      "secondary_effect": "BURN",
      "description": "..."
    }
  },
  "status_effects": {
    "BURN": {
      "max_rank": 6,
      "stackable": false
    }
  }
}
```
The `RuleManager` singleton (`src/config/rule_manager.py`) loads this at startup based on the active language. Access rules anywhere via `from src.config.rule_manager import get_rules`.

### UI translations: `data/i18n/{lang}.json`
All user-facing strings use `translate("key.path", **kwargs)` from `src/utils/localization.py`. Keys are dot-separated paths into the JSON. Example: `translate("messages.damage.absorbed_by_armor", amount=5, loss=3)`.

### Themes & fonts: `src/config/__init__.py`
- Change `ACTIVE_THEME` to switch theme (options: `"Nord Dark"`, `"Gruvbox Dark"`, `"Monokai Dark"`, `"Neutral Light"`, `"Solarized Light"`)
- All theme color dicts live in `src/config/defaults.py` under `THEMES`
- Font sizes are calculated dynamically at startup via `calculate_font_sizes(screen_w, screen_h)` and stored in the module-level `FONTS` dict

### Hotkeys: `data/hotkeys.json`
Key names follow Tkinter's event syntax (e.g. `"<space>"`, `"<Control-d>"`). Loaded by `HotkeyHandler`.

### Enemy presets library: `data/enemies.json`
Structured list of preset enemies importable via the library UI.

### GEW → dice mapping: `src/config/defaults.py`
```python
GEW_TO_DICE = {1: 4, 2: 6, 3: 8, 4: 10, 5: 12, 6: 20}
```
Initiative uses exploding dice: if max face is rolled, roll again and sum (capped at 20 re-rolls).

---

## Persistence & Save Format

- **Autosave:** `saves/autosave.json` — written after *every* engine mutation via `PersistenceHandler.autosave()`
- **Manual saves:** `.json` files, same format, user-chosen path under `saves/`
- **Format:** `engine.get_state()` serializes to a dict; `engine.load_state(dict)` restores it. Characters serialize via `Character.to_dict()` / `Character.from_dict()`. Status effects serialize via `StatusEffect.to_dict()` / `StatusEffect.from_dict()`.
- **Undo/Redo:** `HistoryManager` stores deep-copied `get_state()` snapshots in `undo_stack` / `redo_stack`. Max history size is `MAX_HISTORY` from `src/config/__init__.py`.

---

## Adding a New Damage Type (end-to-end checklist)

1. Add the string value to `DamageType` enum in `src/models/enums.py`
2. Add the type's rules to `data/i18n/de_rules.json` and `en_rules.json` under `"damage_types"`
3. Add description/label strings to `data/i18n/de.json` and `en.json`
4. The damage calculation in `mechanics.calculate_damage()` will automatically pick up the new `ignores_armor` / `ignores_shield` flags — no Python changes needed unless special behavior is required

---

## Test Layout

Tests mirror the `src/` structure under `tests/`. Mocks for the engine and view are in `tests/mocks.py`. Run with `pytest` from the repo root (configured via `pytest.ini`).

---

## Important Constraints

- **All string keys** for damage types and status effects must match between `enums.py` (Python value), `EFFECT_CLASSES` dict, and the `{lang}_rules.json` keys — they are string-compared at runtime.
- **`RuleManager` is a singleton** — call `rule_manager.load_rules()` after a language change, or use the `set_language()` path on `localization_manager` which triggers a reload.
- **UI components must not import from `src/controllers/`** directly — pass callbacks instead to preserve the MVC boundary.
- **Tkinter is single-threaded** — audio playback (pygame) runs in a separate thread via `AudioController`; never call Tkinter methods from that thread.