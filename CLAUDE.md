# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Agent Behaviour

### Grundprinzipien

- **Lesen vor Schreiben.** Vor jeder Änderung die betroffene Datei vollständig lesen. Niemals Code vorschlagen oder ändern, der nicht gelesen wurde.
- **Verstehen vor Implementieren.** Bei unklaren Anforderungen kurz nachfragen — eine falsch implementierte Funktion kostet mehr Zeit als eine Rückfrage.
- **So wenig wie möglich, so viel wie nötig.** Nur das ändern, was explizit gefragt wurde. Kein Refactoring, keine Cleanup-Commits, keine Kommentare in unverändertem Code.
- **Kein Over-Engineering.** Keine abstrakten Basisklassen, Factories oder Helper-Funktionen für Einmal-Logik. Drei ähnliche Zeilen sind besser als eine verfrühte Abstraktion.

### Vorgehen bei Aufgaben

1. **Relevante Dateien lesen** — Architekturdiagramm und Datenfluss-Abschnitte in dieser Datei als Einstieg nutzen.
2. **Abhängigkeiten prüfen** — Verstehen, welche anderen Komponenten von der Änderung betroffen sind (Events, ICombatView, Serialisierung).
3. **Mutation-Pattern einhalten** — `history_manager.save_snapshot()` vor jeder Zustandsänderung.
4. **Tests schreiben oder aktualisieren** — Neue Logik in Core/Controllers/Utils bekommt immer einen Test. UI-Code (Tkinter) wird nicht unit-getestet.
5. **Lokalisierung nicht vergessen** — Jeder neue user-facing String kommt in `de.json` **und** `en.json`.
6. **Linter-Warnungen aus Markdown-Codeblöcken ignorieren** — Der IDE-Linter analysiert Code in `.md`-Dateien fälschlicherweise als Python. Diese Warnungen sind keine echten Fehler.

### Was der Agent NICHT tun soll

- **Keine Commits ohne explizite Aufforderung.** Erst fragen, dann committen.
- **Keine Push-Operationen** ohne ausdrückliche Bestätigung.
- **Keine Umbenennung oder Löschung von Dateien** ohne Rückfrage — es könnte In-Progress-Arbeit sein.
- **Kein `--no-verify`** bei Git-Operationen — Hooks nie überspringen.
- **Keine neuen Abhängigkeiten** (`pip install`) ohne Rückfrage und Eintrag in `requirements.txt`.
- **Keine Docstrings oder Type-Annotations** in Code hinzufügen, der nicht ohnehin geändert wird.
- **Keine Error-Handler** für Szenarien, die intern nicht eintreten können — nur an System-Grenzen (User-Input, externe APIs, Dateisystem) validieren.
- **Kein Zusammenfassen am Ende** was gerade gemacht wurde — der User sieht den Diff selbst.

### Kommunikationsstil

- Antworten auf Deutsch, außer bei Code-Kommentaren (diese bleiben Englisch, da die Codebasis gemischt ist).
- Kurz und direkt. Keine Füllsätze, keine Wiederholung der Frage.
- Bei mehreren unabhängigen Änderungen: parallel ausführen (mehrere Tool-Calls in einer Nachricht).
- Fehler oder Blocker sofort melden — nicht still wiederholen.

### Spielsystem-Kontext

- **0 LP = Tod.** Es gibt keinen Bewusstlos-Zustand — Charaktere mit 0 LP sind sofort tot.
- **AoE-Schaden ist kein gewünschtes Feature** — Mehrfachauswahl in der Liste reicht aus.
- **Keine Angriffs-Presets** — der DM gibt Werte manuell ein.
- Regeländerungen primär in `data/i18n/{lang}_rules.json` vornehmen, nicht in Python.

---

## Commands

```bash
# Run the application
python Combat_Tracker.py

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run a single test file
pytest tests/unit/core/test_engine.py

# Run a specific test by name
pytest tests/unit/core/test_engine.py::TestClassName::test_method_name

# Run tests with coverage
pytest --cov=src
```

---

## Architecture Overview

Tkinter-based PnP combat tracker using **MVC + pub/sub**. There is **no DI framework** — `CombatTracker.__init__` in `src/ui/main_window.py` is the explicit composition root that manually wires all components together.

```
Combat_Tracker.py                  ← entry point, creates tk.Tk + CombatTracker
└── src/ui/main_window.py          ← CombatTracker: composition root, wires everything
    │
    ├── src/core/engine.py         ← CombatEngine: owns character list, delegates to sub-systems
    ├── src/core/turn_manager.py   ← TurnManager: rounds, initiative order, status ticks
    ├── src/core/history.py        ← HistoryManager: undo/redo via deep-copied state snapshots
    ├── src/core/event_manager.py  ← EventManager: pub/sub (UPDATE, LOG, TURN_CHANGE)
    ├── src/core/mechanics.py      ← calculate_damage(), wuerfle_initiative() — pure functions
    │
    ├── src/controllers/           ← one handler per concern
    │   ├── combat_action_handler.py   ← damage, healing, status, next_turn
    │   ├── character_management_handler.py
    │   ├── persistence.py         ← autosave, manual save/load, crash detection
    │   ├── import_handler.py      ← Excel import
    │   ├── audio_controller.py    ← pygame audio, runs in separate thread
    │   ├── hotkey_handler.py
    │   └── library_handler.py     ← builds embedded library, delegates to tab-controllers
    │       ├── library_markdown_tab.py
    │       ├── library_pdf_tab.py
    │       └── library_import_tab.py  ← enemy search/filter + Encounter Generator
    │
    ├── src/ui/main_view.py        ← MainView: implements ICombatView protocol
    │   ├── ControlBar             ← always-visible top bar (Quick-Add, initiative, undo/redo)
    │   └── Notebook (3 tabs)
    │       ├── CombatTab          ← CharacterList | ActionPanel + AudioPlayerWidget + Log + DiceRoller
    │       ├── Library (embedded) ← via library_handler.build_embedded()
    │       └── DMNotesPanel       ← Markdown editor with file tree, tags, templates
    │
    ├── src/models/
    │   ├── character.py           ← Character dataclass, to_dict/from_dict
    │   ├── status_effects.py      ← StatusEffect base + all subclasses + EFFECT_CLASSES dict
    │   ├── enums.py               ← DamageType, StatusEffectType, CharacterType, …
    │   └── combat_results.py      ← DamageResult dataclass
    │
    ├── src/utils/
    │   ├── db_manager.py          ← DatabaseManager singleton (SQLite + FTS5), library index
    │   ├── save_manager.py        ← SaveManager: atomic writes, versioned format
    │   ├── library_index.py       ← LibraryIndex: scans files, feeds DatabaseManager
    │   ├── localization.py        ← translate(), LocalizationManager singleton
    │   ├── enemy_repository.py    ← loads data/enemies.json
    │   ├── navigation_manager.py  ← browser-style back/forward for library
    │   └── markdown_utils.py      ← Markdown → Tkinter text rendering
    │
    └── src/config/
        ├── __init__.py            ← COLORS, FONTS, ACTIVE_THEME, MAX_HISTORY, window sizes
        ├── defaults.py            ← THEMES dict, GEW_TO_DICE, MAX_GEW
        └── rule_manager.py        ← RuleManager singleton, loads {lang}_rules.json
```

---

## Key Design Patterns

### 1. Every mutating action follows this exact pattern

```python
self.history_manager.save_snapshot()   # ALWAYS snapshot BEFORE the mutation
self.engine.do_something()             # mutate state via engine/turn_manager methods
# engine.notify(EventType.UPDATE) fires automatically inside engine methods
```

**Never skip the snapshot.** Without it, undo/redo breaks silently.
**Never mutate `engine.characters` directly from a controller** — use engine methods.

### 2. Event flow: core → UI

`CombatEngine` fires events via `EventManager`. UI components subscribe:

```python
engine.subscribe(EventType.UPDATE, self.update_listbox)
engine.subscribe(EventType.LOG, self.log_message)
engine.subscribe(EventType.TURN_CHANGE, self.on_turn_change)
```

Data flows **one way**: Core fires → UI reacts. UI never pushes state into the core.

### 3. `ICombatView` protocol (`src/ui/interfaces.py`)

Controllers communicate with the UI **exclusively** through this interface. Never import concrete UI classes in controllers. Key methods:

| Method | Returns | Purpose |
| :--- | :--- | :--- |
| `get_damage_data()` | `(int, str, str)` | Total damage, details string, damage type |
| `get_status_input()` | `dict` | `rank`, `duration`, `effect` |
| `get_selected_char_id()` | `str \| None` | Single selection |
| `get_selected_char_ids()` | `list[str]` | Multi-selection |
| `get_overheal()` | `bool` | Allow healing above max LP |
| `ask_secondary_effect(effect, chars)` | `list[Character]` | Which chars receive the secondary effect |
| `log_message(msg)` | — | Append to combat log |
| `update_listbox()` | — | Refresh character list UI |

### 4. MVC boundary rule

```
src/ui/       → may import from src/controllers/ only via callbacks passed in __init__
src/controllers/ → may import from src/core/, src/models/, src/utils/, src/config/
src/core/     → must NOT import from src/ui/ or src/controllers/
```

UI components **must not import from `src/controllers/`** directly. Pass callbacks instead.

---

## Data Flow: Damage Calculation

```
CombatActionHandler.deal_damage()
  → view.get_damage_data()              # reads UI inputs
  → engine.apply_damage(char, amount, damage_type, rank)
      → character.apply_damage(dmg, damage_type, rank)
          → mechanics.calculate_damage(character, dmg, damage_type, rank)
              → RuleManager.get_rules()["damage_types"][damage_type]
              → SP → RP → LP chain
              → returns DamageResult
      → engine fires EventType.UPDATE + EventType.LOG
  → if DamageResult.secondary_effect:
      → view.ask_secondary_effect()     # SecondaryEffectDialog
      → combat_handler.apply_status()   # on confirmed targets
```

**SP → RP → LP chain in `mechanics.calculate_damage()`:**
1. **Shield (SP):** absorbs up to `character.sp`, 1:1. Skipped if `ignores_shield: true`.
2. **Armor (RP):** absorbs up to `character.rp * 2` remaining damage; loses `(absorbed + 1) // 2` durability. Skipped if `ignores_armor: true`.
3. **HP (LP):** remainder hits LP. If LP ≤ 0 → `DamageResult.is_dead = True`.

---

## Data Flow: Status Effects

Status effects tick in `TurnManager._update_character_status()`, called at the **start of each character's turn** via `next_turn()`.

Each effect's `apply_round_effect(character)` is called:
- Returns a log string
- May deal damage (`DIRECT` for Poison, `NORMAL` for Burn/Bleed)
- May modify state (Stun → `character.skip_turns = 1`, Erosion → reduces `character.max_lp`)
- Decrements duration; removes itself when expired

**Stacking behaviour** (from `{lang}_rules.json`):
- `stackable: true` → new application increases rank or extends duration
- `stackable: false` → new application refreshes duration only

---

## Data Flow: Healing

```
CombatActionHandler.apply_healing()
  → view.get_action_value()
  → view.get_overheal()           # if True: LP may exceed max_lp
  → engine.apply_healing(char, amount, allow_overheal)
      → character.lp = min(max_lp, lp + amount)   # or uncapped if overheal
      → engine fires EventType.UPDATE + EventType.LOG
```

---

## Persistence & Save Format

### Save files
- **Autosave:** `saves/autosave.json` — written after **every** engine mutation via `PersistenceHandler.autosave()`
- **Manual saves:** user-chosen `.json` path under `saves/`
- **Format (on disk):** `{"version": <int>, "state": <engine_state_dict>}`
  `SaveManager` wraps and unwraps this automatically; older files without `version` are loaded as-is.
- **Atomic write:** `SaveManager` writes to a `.tmp` file first, then renames — a crash during save never corrupts the target file.

### Serialisation
- `engine.get_state()` → dict; `engine.load_state(dict)` restores
- `Character.to_dict()` / `Character.from_dict()`
- `StatusEffect.to_dict()` / `StatusEffect.from_dict()` — uses `EFFECT_CLASSES` registry for reconstruction

### Undo/Redo
`HistoryManager` stores deep-copied `get_state()` snapshots in `undo_stack` / `redo_stack`.
Max size: `MAX_HISTORY` in `src/config/__init__.py`.

---

## Database Layer (Library Index)

`DatabaseManager` (`src/utils/db_manager.py`) is a **singleton** backed by SQLite with FTS5.

```python
from src.utils.db_manager import DatabaseManager
db = DatabaseManager("data/library.db")   # returns the singleton
db.conn                                    # raw sqlite3.Connection
```

- Schema is created/migrated automatically on first access (`_migrate()` is idempotent).
- `library_fts` is a virtual FTS5 table for full-text search across all indexed files.
- `LibraryIndex` (`src/utils/library_index.py`) scans `data/` and populates `DatabaseManager`.
- **Never call `DatabaseManager()` with a different path after the singleton is created.**

---

## Where Rules & Config Live

| File | What lives here |
| :--- | :--- |
| `data/i18n/{lang}_rules.json` | Damage types (`ignores_armor`, `ignores_shield`, `secondary_effect`) and status effects (`max_rank`, `stackable`). **Primary place for mechanic changes.** |
| `data/i18n/{lang}.json` | All UI strings. Access via `translate("key.path", **kwargs)`. |
| `data/enemies.json` | Enemy presets for library and Encounter Generator. |
| `data/hotkeys.json` | Tkinter event syntax, e.g. `"<Control-d>"`. Loaded by `HotkeyHandler`. |
| `src/config/__init__.py` | `ACTIVE_THEME`, `MAX_HISTORY`, `FONTS`, `COLORS`, window sizes. |
| `src/config/defaults.py` | `THEMES` dict, `GEW_TO_DICE`, `MAX_GEW`. |

**GEW → dice:** `{1: 4, 2: 6, 3: 8, 4: 10, 5: 12, 6: 20}` — exploding dice, max 20 re-rolls.

**Themes:** Change `ACTIVE_THEME` in `src/config/__init__.py`. Available: `"Nord Dark"`, `"Nord Light"`, `"Gruvbox Dark"`, `"Gruvbox Light"`, `"Monokai Dark"`, `"Neutral Dark"`, `"Neutral Light"`, `"Solarized Light"`.

---

## Checklists for Common Tasks

### Add a new Damage Type

1. Add string value to `DamageType` enum in `src/models/enums.py`
2. Add rules to `data/i18n/de_rules.json` **and** `en_rules.json` under `"damage_types"`
3. Add label/description to `data/i18n/de.json` **and** `en.json`
4. Done — `mechanics.calculate_damage()` picks up `ignores_armor`/`ignores_shield` automatically. Add a Python subclass only for non-standard behaviour.

### Add a new Status Effect

1. Add name to `StatusEffectType` enum in `src/models/enums.py`
2. Create subclass of `StatusEffect` in `src/models/status_effects.py` — implement `apply_round_effect(character) -> str`
3. Register in `EFFECT_CLASSES` dict at the bottom of `status_effects.py`
4. Add config to `de_rules.json` **and** `en_rules.json` under `"status_effects"` (`max_rank`, `stackable`)
5. Add translation strings to `de.json` **and** `en.json` under `"messages.status"`

### Add a new Controller / Handler

1. Create `src/controllers/my_handler.py` — accept `engine`, `view`, `history_manager` in `__init__`
2. Instantiate and wire in `CombatTracker.__init__` (`src/ui/main_window.py`)
3. Pass callbacks into UI components — never let UI import the handler directly
4. Write tests in `tests/unit/controllers/test_my_handler.py` using mocks from `tests/unit/mocks.py`

---

## Testing

### Layout

```
tests/
├── unit/
│   ├── core/          test_engine, test_turn_manager, test_history, test_event_manager, test_mechanics
│   ├── models/        test_character, test_status_effects
│   ├── controllers/   test_combat_action_handler, test_character_management_handler,
│   │                  test_import_handler, test_persistence, test_audio_controller,
│   │                  test_hotkey_handler, test_library_handler
│   ├── utils/         test_localization, test_navigation_manager, test_enemy_repository,
│   │                  test_library_index, test_markdown_utils, test_ui_utils,
│   │                  test_db_manager, test_save_manager
│   └── config/        test_rule_manager, test_config
└── integration/
    └── test_combat_integration.py   ← no mocks, real objects only
```

Mocks for engine and view: `tests/unit/mocks.py`.

### Rules for writing tests

- **Unit tests** mock the engine and view via `tests/unit/mocks.py` — keep them fast and isolated.
- **Integration tests** use real objects end-to-end (`tests/integration/`) — no mocking. These catch cross-layer bugs that unit tests miss.
- `DatabaseManager` tests use `":memory:"` and reset the singleton in a `reset_singleton` fixture.
- `SaveManager` tests use `tmp_path` (pytest built-in) — never write to `saves/` in tests.
- Pure UI code (`ToolTip`, `ScrollableFrame`, dialog classes) is **not** unit tested — Tkinter requires a display.
- After writing new code, always check whether an existing test covers it before writing a new one.

---

## Important Constraints

- **String key consistency:** Damage type and status effect keys must match **exactly** between `enums.py` values, `EFFECT_CLASSES` dict keys, and `{lang}_rules.json` keys — they are string-compared at runtime. A mismatch causes a silent KeyError.
- **`RuleManager` is a singleton** — after a language change, `rule_manager.load_rules()` is called automatically via `localization_manager.set_language()`. Do not call it manually elsewhere.
- **`DatabaseManager` is a singleton** — always access via `DatabaseManager(path)` (returns the existing instance if already created). Never instantiate directly with `__new__`.
- **Tkinter is single-threaded** — `AudioController` (pygame) runs in its own thread. Never call Tkinter widget methods from inside `AudioController` callbacks. Use `root.after()` to schedule UI updates from threads.
- **UI components must not import from `src/controllers/`** — pass callbacks in `__init__` to preserve the MVC boundary.
- **`history_manager.save_snapshot()` before every mutation** — skipping it silently breaks undo/redo for that action.
- **Autosave is triggered by `PersistenceHandler`**, which subscribes to `EventType.UPDATE`. Do not call `autosave()` manually in controllers — the event subscription handles it.
- **`translate()` for all user-facing strings** — never hardcode German or English text in Python source. Add the key to both `de.json` and `en.json`.