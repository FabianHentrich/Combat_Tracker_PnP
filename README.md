# ⚔️ PnP Combat Tracker

> ⚠️ **Spoiler-Warnung:**
> In den mitgelieferten Daten befinden sich vollständige Kampagnen, One-Shots und Abenteuer. Wer als Spieler an einer der enthaltenen Kampagnen teilnehmen möchte, sollte die DM-Notizen und Bibliothek mit Vorsicht genießen. Die Bibliothek lässt sich öffnen ohne zwingend gespoilert zu werden — als Spieler empfiehlt sich jedoch ausschließlich der Tab *Regelwerk*.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

Ein feature-reicher Combat Tracker für Pen & Paper Rollenspiele, entwickelt mit Python und Tkinter. Das Tool wurde primär für ein **eigenes PnP-Regelwerk** entwickelt, ist aber auf andere Systeme anpassbar.

> ℹ️ Das Regelwerk und eine beispielhafte Spielwelt (Orte, Gegner, NPCs, Gegenstände, Götter u.v.m.) sind direkt im Programm einsehbar. Bei Interesse oder Fragen einfach eine E-Mail schreiben!

---

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Installation & Start](#-installation--start)
- [Benutzung](#-benutzung)
- [Das Spielsystem](#-das-spielsystem)
  - [Charaktererschaffung & Level](#charaktererschaffung--level)
  - [RANG & Würfelmechanik](#rang--würfelmechanik)
  - [Proben](#proben)
  - [Kampfablauf](#kampfablauf)
  - [Attribute & Verteidigung](#attribute--verteidigung)
  - [Angriff & Parade](#angriff--parade)
  - [Schadensberechnung](#schadensberechnung)
  - [Schadenstypen](#schadenstypen)
  - [Status-Effekte](#status-effekte)
- [Musik-Player](#-musik-player)
- [Konfiguration & Anpassung](#-konfiguration--anpassung)
- [Hotkeys](#-hotkeys)
- [Entwickler-Infos](#-entwickler-infos)
- [Lizenz](#-lizenz)

---

## ✨ Features

### Kampfverwaltung
- **Initiative-Verwaltung:** Automatisches Würfeln und Sortieren per Exploding-Dice-System basierend auf dem GEWANDTHEIT-Wert.
- **Erweitertes Schadenssystem:** Dreistufige Schadenskette — Schild (SP) → Rüstung (RP) → Leben (LP) — mit 8 konfigurierbaren Schadenstypen.
- **Sekundäreffekt-Dialog:** Nach einem Elementar-Treffer erscheint automatisch ein Dialog zum Anwenden des Sekundäreffekts (z.B. Verbrennung nach Feuerschaden) inklusive Rang- und Dauerauswahl.
- **Überheilung:** Heilung kann optional über die maximalen LP hinausgehen (z.B. durch magische Heilzauber).
- **Dynamische Schadenseingabe:** Kombiniere mehrere Schadensarten in einer Aktion (z.B. "10 Feuer + 5 Kälte").
- **Mehrfachauswahl:** Wende Aktionen auf mehrere Charaktere gleichzeitig an (`Strg+Klick` / `Shift+Klick`).
- **Status-Effekte:** 11 Zustände mit automatischer Rundenverwaltung, Rängen (1–6) und konfigurierbarer Stapelbarkeit.
- **Undo/Redo:** Jede Aktion ist rückgängig machbar — Snapshots werden vor jeder Mutation gespeichert.

### Charakter-Management
- **Charakter-Verwaltung:** Hinzufügen, Bearbeiten (Doppelklick) und Löschen von Spielern, Gegnern und NPCs.
- **Excel-Import:** Charaktere und Gegner direkt aus `.xlsx`-Dateien importieren.
- **Gegner direkt aus der Bibliothek hinzufügen:** Der *Gegner-Import*-Tab bietet Volltext­suche, Kategorie-/Typ-/Level-Filter und fügt Gegner per Knopfdruck mit gewürfelter Initiative in den Kampf ein.
- **Encounter Generator:** Gegner zufällig nach Kategorie, Typ und Level-Range generieren — ideal für spontane Kämpfe.

### Bibliothek & Notizen
- **DM-Notizen:** Eigenes Panel für Kampagnenplanung (Markdown, Dateibaum, Undo/Redo, Autosave, Drag & Drop, Umbenennen/Löschen). Neue Notizen aus Vorlagen (NPC, Ort, Quest, Fraktion) erstellen. Notizen per Tag filtern. Schnellzugriff auf zuletzt geöffnete Dateien.
- **Markdown & PDF Bibliothek:** Regeln, Items, NPCs, Orte und mehr als Markdown-Dateien oder direkt als PDF (z.B. das Regelbuch) im Tool anzeigen.
- **SQLite-Volltext­suche (FTS5):** Alle Markdown-Dateien und PDFs werden in einer lokalen SQLite-Datenbank indexiert. Die Suche liefert Treffer in Echtzeit; der Index wird bei Dateiänderungen automatisch aktualisiert.
- **Intelligente Verlinkung:** `[[Link]]` öffnet die Zieldatei direkt; `[[rules:123]]` springt zur angegebenen Seite im Regelwerks-PDF.
- **Versionierung:** Notizänderungen werden automatisch versioniert (bis zu 20 Schritte rückgängig, konfigurierbar in `src/config/__init__.py`).

### Persistenz & Komfort
- **Persistenz & Autosave:** Der Kampfzustand wird **nach jeder Änderung** atomar in `saves/autosave.json` gespeichert (Temp-Datei → Rename, kein Datenverlust bei Absturz). Das Dateiformat ist versioniert für Vorwärtskompatibilität.
- **Mehrsprachigkeit:** Deutsch und Englisch, jederzeit ohne Kampfstatusverlust umschaltbar.
- **Absturzerkennung:** Automatische Erkennung eines vorherigen Absturzes (Lock-File) mit Wiederherstellungsangebot.
- **Dice Roller:** Integrierter Würfelsimulator (W4 bis W100) mit Exploding-Dice.
- **Themes:** 8 Farbschemata (4 Dark, 4 Light), vollständig über alle UI-Elemente hinweg.
- **Responsive UI:** Schriftgrößen skalieren dynamisch basierend auf der Bildschirmauflösung.
- **Musik-Player:** Integrierter Audio-Player für lokale Dateien (MP3, WAV, OGG) mit Playlist, Loop-Modi und Drag & Drop.

---

## 🚀 Installation & Start

### Voraussetzungen
- Python 3.8 oder höher
- `tkinter` (bei Windows/macOS meist im Python-Installer enthalten; Linux: `sudo apt-get install python3-tk`)

### Schritte

```bash
# 1. Repository klonen
git clone https://github.com/DeinUsername/Combat_Tracker_PnP.git
cd Combat_Tracker_PnP

# 2. Virtuelle Umgebung erstellen (empfohlen)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Programm starten
python Combat_Tracker.py
```

---

## 🎮 Benutzung

Das Programm besteht aus einer **immer sichtbaren Kontroll-Leiste** oben und einem **Notebook mit drei Tabs** darunter.

### Kontroll-Leiste (immer sichtbar)
Enthält die zentralen Kampf-Buttons sowie das **Schnellhinzufügen-Panel**:
- Initiative würfeln / zurücksetzen (alle, nur Gegner, nur Spieler)
- **Nächster Zug** (`Leertaste`) — tickt Status-Effekte automatisch ab
- Undo / Redo
- Rundenanzeige
- Schnellhinzufügen: Name, Typ, LP, GEW direkt eingeben → Charakter sofort in den Kampf

### Tab ⚔ Kampf
Das Haupt-Tab, zweispaltig aufgeteilt:

**Linke Spalte:**
| Bereich | Beschreibung |
| :--- | :--- |
| **Initiative-Liste** | Alle Charaktere in Zugreihenfolge. Aktiver Charakter hervorgehoben. Doppelklick öffnet Bearbeitungs-Dialog. Mehrfachauswahl via `Strg`/`Shift`. |
| **Kampfprotokoll** | Detailliertes Protokoll aller Ereignisse (Schaden, Rundenwechsel, Effekte, Heilung). |
| **Dice Roller** | Würfelsimulator (W4–W100) mit Exploding-Dice, direkt neben dem Log. |

**Rechte Spalte:**
| Bereich | Beschreibung |
| :--- | :--- |
| **Aktions-Panel** | Schaden, Heilung und Status-Effekte auf ausgewählte Charaktere anwenden. Mehrere Schadenskomponenten kombinierbar (z.B. 10 Feuer + 5 Kälte). |
| **Musik-Player** | Playlist, Loop-Modi, Lautstärke — fixiert am unteren Rand der rechten Spalte. |

### Tab 📚 Bibliothek
Integrierte Wiki mit Tabs: *Regelwerk, Gegenstände, Gegner (Info), NPCs, Orte, Organisationen, Götter* sowie **Gegner-Import** (Suche, Filter, Encounter Generator, Direkt-Import in den Kampf).

### Tab 📝 DM-Notizen
Markdown-Editor mit Dateibaum, Tag-Filter, Vorlagen-Auswahl, Undo/Redo, Autosave, Drag & Drop und Schnellzugriff auf zuletzt geöffnete Dateien.

### Typischer Ablauf
1. Charaktere hinzufügen — Schnellhinzufügen in der Kontroll-Leiste, Excel-Import oder aus dem Gegner-Import-Tab.
2. **Initiative würfeln** → Liste sortiert sich automatisch.
3. **Nächster Zug** (`Leertaste`) — Status-Effekte ticken automatisch.
4. Ziel in der Liste auswählen → Schaden-/Heilungswerte im Aktions-Panel eingeben → Anwenden.
5. Bei Elementarschaden: Sekundäreffekt-Dialog bestätigen oder abbrechen.
6. Kampf über das Datei-Menü speichern — oder einfach den Autosave nutzen.

---

## 🎲 Das Spielsystem

Das Tool wurde für ein eigenes Regelwerk entwickelt. Dieser Abschnitt erklärt die Spielmechaniken, die das Programm abbildet.

### Charaktererschaffung & Level

Jeder Charakter startet auf **Level 1** mit:
- **15 Talentpunkte** (für STÄRKE, GEWANDTHEIT, KAMPF, etc.)
- **15 Skill- oder Zauberpunkte** (Klassen-abhängig)
- bis zu **2 Eigenheiten** (positive oder negative Charakterzüge)

**LP-Berechnung:** `20 + STÄRKE-Würfelwurf`

| Level | Skill-/Zauberpunkte | Bonuspunkte | AP / Mana |
| :---: | :---: | :---: | :---: |
| 1 | 10 | — | 50 |
| 2 | 20 | +5 | 60 |
| 3 | 35 | — | 70 |
| 4 | 45 | +5 | 80 |
| 5 | 60 | — | 90 |

Ab Level 2 kann eine **Nebenklasse** gewählt werden. **Magierklassen** erlernen Zauber, **nichtmagische Klassen** erlernen Skills.

**Empfohlene Punktvergabe nach Abenteuern:**
- Talentpunkte: 2–3 pro Abenteuer
- Skill-/Zauberpunkte: 3–5 pro Abenteuer (+ Boni für gutes Roleplay, kreative Lösungen, etc.)

---

### RANG & Würfelmechanik

Der **RANG** (Fähigkeitsrang) gibt an, wie gut ein Charakter ein Talent, einen Zauber oder Skill beherrscht. Er bestimmt die **Würfelgröße** und die **Effektstärke**.

| RANG | Würfel | Erfolgswahrscheinlichkeit | Bedeutung |
| :---: | :---: | :---: | :--- |
| 1 | W4 | 25 % | Anfänger |
| 2 | W6 | 50 % | Normal |
| 3 | W8 | 62,5 % | Beruf |
| 4 | W10 | 70 % | Elite |
| 5 | W12 | 75 % | Meisterhaft |
| 6 | W20 | 80 % | Legendär |

> RANG 6 ist der **Legendäre RANG** und nur unter besonderen Umständen erreichbar.

**Exploding Dice (Ass-Mechanik):** Wird die höchstmögliche Augenzahl eines Würfels geworfen, darf erneut gewürfelt und das Ergebnis addiert werden (Initiative: max. 20 Wiederholungen).

---

### Proben

Eine **Probe** ist ein Würfelwurf gegen eine Herausforderung:

1. Der Spieler würfelt mit dem Würfel seines Fähigkeitsrangs.
2. Standardschwelle: **mindestens eine 4** für Erfolg.
3. Modifikatoren (Bonus/Malus) durch Gegenstände, Zauber oder Spielleiter-Entscheidung.

**Wurfzahl-Ergebnisse bei Zauber-/Skill-Kosten:**

| Wurfergebnis | Ergebnis | Kosten |
| :---: | :--- | :---: |
| 1–3 | misslingt | halbe Kosten |
| 4–6 | gelingt | volle Kosten |
| 7–9 | gelingt | halbe Kosten |
| 10+ | gelingt | keine Kosten |

---

### Kampfablauf

- **Runden:** Eine Runde entspricht ca. 5–6 Sekunden Echtzeit.
- **Aktionen pro Zug:** 1 **Aktion** (Angriff, Bewegen, Zauber) + 1 **Bonusaktion** (Trank, Ausrüstung wechseln, etc.).
- **Initiative:** Zu Kampfbeginn würfelt jeder auf GEWANDTHEIT (Exploding Dice). Höchster Wert beginnt.

**GEW → Initiative-Würfel:**

| GEW | Würfel |
| :---: | :---: |
| 1 | W4 |
| 2 | W6 |
| 3 | W8 |
| 4 | W10 |
| 5 | W12 |
| 6+ | W20 |

---

### Attribute & Verteidigung

| Attribut | Beschreibung |
| :--- | :--- |
| **LP** (Lebenspunkte) | Vitalität des Charakters. Bei 0 LP stirbt der Charakter. Regeneration: 2× STÄRKE-Wert pro Nachtruhe. |
| **RP** (Rüstungspunkte) | Physische Rüstung. 1 RP absorbiert 2 Schaden, nutzt sich aber ab (Haltbarkeit sinkt). Muss repariert werden. |
| **SP** (Schildpunkte) | Magischer/energetischer Schild. 1 SP absorbiert 1 Schaden. Kein automatisches Aufladen — erfordert Zauber oder Items. |
| **STÄRKE** | Bestimmt LP und den Regenerationswert. |
| **GEWANDTHEIT (GEW)** | Bestimmt den Initiative-Würfel und den Ausweichen-Wurf. |
| **KAMPF** | Bestimmt Angriffs- und Parade-Würfe. |

---

### Angriff & Parade

1. **Angreifer** würfelt KAMPF → muss mindestens eine **4** erzielen.
2. **Verteidiger** wählt:
   - **Parade:** KAMPF-Wurf muss die **Wurfzahl des Angreifers** übertreffen. Bei Erfolg wird der gesamte Schaden verhindert.
   - **Ausweichen:** GEWANDTHEIT-Wurf muss die Wurfzahl des Angreifers übertreffen.

**Magische Waffen:** Geben +2 auf die Wurfzahl bei der Parade (Vorteil gilt erst nach einem Treffer mit mindestens 4).

---

### Schadensberechnung

Schaden wird immer in dieser Reihenfolge verrechnet:

```
1. Schild (SP)   — absorbiert Schaden 1:1, solange SP > 0
2. Rüstung (RP)  — absorbiert bis zu RP × 2 verbleibenden Schaden
                   Rüstungsverlust: (absorbierter Schaden + 1) / 2 RP
3. Leben (LP)    — Resschaden geht direkt auf LP
```

**Beispiel:** 30 Schaden, Charakter hat SP=10, RP=5
- Schild: absorbiert 10 → SP=0, verbleibend=20
- Rüstung: absorbiert min(10, 20)=10 → RP-Verlust=(10+1)//2=5, RP=0, verbleibend=10
- Leben: 10 LP-Verlust → LP−10

---

### Schadenstypen

Schadenstypen und ihre Regeln sind in `data/i18n/de_rules.json` definiert und ohne Code-Änderungen anpassbar.

| Typ | Bezeichnung | Schild (SP) | Rüstung (RP) | Sekundäreffekt |
| :--- | :--- | :---: | :---: | :--- |
| `NORMAL` | Waffenschaden | ✓ | ✓ | — |
| `PIERCING` | Durchdringend | ✓ | ✗ | — |
| `DIRECT` | Direktschaden | ✗ | ✗ | — |
| `FIRE` | Feuer | ✓ | ✓ | Verbrennung |
| `COLD` | Kälte | ✓ | ✓ | Unterkühlung |
| `LIGHTNING` | Blitz | ✓ | ✓ | Betäubung |
| `POISON` | Gift | ✓ | ✓ | Vergiftung |
| `DECAY` | Verwesung | ✓ | ✓ | Erosion |

> **Sekundäreffekte** haben eine Auslösechance abhängig vom Rang der Fähigkeit. Nach einem Treffer erscheint im Tool automatisch ein Dialog, um den Effekt direkt anzuwenden.

---

### Status-Effekte

Effekte ticken zu Beginn des jeweiligen Charakterzuges. Jeder Effekt hat eine **Dauer** (Runden) und einen **Rang** (Stärke 1–6).

| Effekt | Symbol | Wirkung | Max. Rang | Stapelbar |
| :--- | :---: | :--- | :---: | :---: |
| **Vergiftung** | ☠️ | `Rang` Direktschaden pro Runde | 5 | Ja |
| **Verbrennung** | 🔥 | `Rang` Normaler Schaden pro Runde | 5 | Ja |
| **Blutung** | 🩸 | Normaler Schaden, steigt jede Runde um +1 (`Rang/2 + Runden−1`) | 5 | Ja |
| **Erosion** | 🧪 | Dauerhafter Verlust von `Rang × W4` max. LP + gleicher Betrag als Direktschaden | 5 | Ja |
| **Unterkühlung** | ❄️ | Verlust der Bonusaktion für `Rang` Runden | 5 | Nein |
| **Betäubung** | ⚡ | Verlust aller Aktionen für 1 Runde | 1 | Nein |
| **Erschöpfung** | 🥵 | −2 auf GEWANDTHEIT für 1 Runde | 1 | Nein |
| **Verwirrung** | 🤪 | −1 auf KAMPF-Proben | 1 | Nein |
| **Blendung** | 🙈 | Malus auf Aktionen/Angriffe je nach Rang (1–5) | 5 | Nein |
| **Entwaffnet** | ⚔️ | Geführte Waffe kann nicht eingesetzt werden | 1 | Nein |
| **Regeneration** | 💚 | Stellt zu Beginn des Zuges `Rang` LP wieder her | 5 | Ja |

> Erhält ein Charakter einen Effekt, den er bereits hat, wird je nach Konfiguration die Dauer verlängert oder der Rang erhöht.

---

## 🎵 Musik-Player

Der integrierte Musik-Player sitzt oben rechts im Hauptfenster.

- **Lokale Wiedergabe:** MP3, WAV, OGG direkt vom Computer.
- **Playlist-Management:** Dateien über das Zahnrad-Symbol hinzufügen; Reihenfolge per Drag & Drop ändern.
- **Loop-Modi:**
  - 🔁 **Einzeln (Inf):** Aktuellen Titel endlos wiederholen.
  - 🔢 **Anzahl (×N):** Titel N-mal wiederholen, dann weiter.
  - 🔄 **Playlist:** Playlist von oben nach unten durchspielen.
- **Steuerung:** Play/Pause, Vor/Zurück, Lautstärke, Mute — alle direkt im Hauptfenster per Button oder Hotkey.
- **Tabletop Audio:** Button öffnet [Tabletop Audio](https://tabletopaudio.com/) im Browser.

---

## ⚙️ Konfiguration & Anpassung

Das Tool ist vollständig über JSON-Dateien im `data/`-Verzeichnis konfigurierbar — kein Code anfassen nötig.

| Datei / Ort | Inhalt |
| :--- | :--- |
| `data/i18n/de_rules.json` / `en_rules.json` | **Spielregeln:** Schadenstypen (`ignores_armor`, `ignores_shield`, `secondary_effect`) und Status-Effekte (`max_rank`, `stackable`). Primäre Anlaufstelle zum Anpassen der Spielmechanik. |
| `data/i18n/de.json` / `en.json` | UI-Übersetzungen. Alle angezeigten Texte. |
| `data/enemies.json` | Gegner-Presets für die Bibliothek und den Gegner-Import-Tab. |
| `data/hotkeys.json` | Tastenkürzel (Tkinter-Syntax, z.B. `"<Control-d>"`). |
| `data/` Unterordner | Markdown-Dateien für die Bibliothek (Regeln, Items, NPCs, Orte, etc.). |
| `src/config/__init__.py` | Aktives Theme (`ACTIVE_THEME`), maximale Undo-History (`MAX_HISTORY`). |

### Themes

| Dark Themes | Light Themes |
| :--- | :--- |
| `Nord Dark` (Standard) | `Nord Light` |
| `Gruvbox Dark` | `Gruvbox Light` |
| `Monokai Dark` | `Solarized Light` |
| `Neutral Dark` | `Neutral Light` |

### Neue Schadensart hinzufügen (Checkliste)

1. Wert zur `DamageType`-Enum in `src/models/enums.py` hinzufügen.
2. Eintrag in `data/i18n/de_rules.json` und `en_rules.json` unter `"damage_types"` anlegen.
3. Übersetzungsstrings in `data/i18n/de.json` und `en.json` ergänzen.
4. Fertig — `calculate_damage()` wertet `ignores_armor`/`ignores_shield` automatisch aus.

### Neuen Status-Effekt hinzufügen (Checkliste)

1. Name zur `StatusEffectType`-Enum in `src/models/enums.py` hinzufügen.
2. Subklasse von `StatusEffect` in `src/models/status_effects.py` erstellen (`apply_round_effect()`).
3. In `EFFECT_CLASSES`-Dict am Ende von `status_effects.py` registrieren.
4. Konfiguration in `de_rules.json` und `en_rules.json` unter `"status_effects"` ergänzen.
5. Übersetzungsstrings in `de.json` / `en.json` unter `"messages.status"` ergänzen.

---

## ⌨️ Hotkeys

| Aktion | Standard-Hotkey |
| :--- | :---: |
| **Nächster Zug** | `Leertaste` |
| **Rückgängig (Undo)** | `Strg + Z` |
| **Wiederholen (Redo)** | `Strg + Y` |
| **Charakter löschen** | `Entf` |
| **Fokus auf Schadenseingabe** | `Strg + D` |
| **Musik Play/Pause** | `Strg + P` |
| **Nächster Titel** | `Strg + →` |
| **Vorheriger Titel** | `Strg + ←` |
| **Lautstärke +** | `Strg + ↑` |
| **Lautstärke −** | `Strg + ↓` |
| **Stummschalten** | `Strg + M` |

*(Alle Hotkeys in `data/hotkeys.json` anpassbar — Tkinter-Syntax)*

---

## 🛠️ Entwickler-Infos

### Projektstruktur

```
Combat_Tracker.py          ← Einstiegspunkt
├── src/
│   ├── core/              ← Business-Logik (Engine, Mechaniken, History, Events)
│   ├── models/            ← Datenmodelle (Character, StatusEffects, Enums)
│   ├── controllers/       ← Handler (Damage, Import, Audio, Hotkeys, Persistenz, Bibliothek)
│   ├── ui/                ← Tkinter-UI, getrennt von Logik
│   ├── config/            ← Themes, Schriftarten, Konstanten
│   └── utils/             ← Logger, Lokalisierung, DB-Manager, Save-Manager
├── data/                  ← JSON-Konfiguration und Markdown-Bibliothek
├── saves/                 ← Spielstände und Autosaves
├── logs/                  ← Anwendungslogs
└── tests/                 ← Unit- und Integrationstests (pytest)
```

### Architektur-Highlights

- **Composition Root:** `MainWindow` (`src/ui/main_window.py`) ist der explizite Verdrahtungspunkt — alle Abhängigkeiten werden manuell instanziiert und injiziert, kein Framework.
- **MVC + Pub/Sub:** `CombatEngine` feuert Events (`UPDATE`, `LOG`, `TURN_CHANGE`); UI-Komponenten subscriben. UI mutiert nie direkt `engine.characters`.
- **`ICombatView`-Protokoll:** Controller kommunizieren mit der UI ausschließlich über dieses Interface (`src/ui/interfaces.py`).
- **UUIDs:** Charaktere werden intern per UUID identifiziert, um Namenskonflikte zu vermeiden.
- **Datengetriebenes Design:** Schadenstypen, Status-Effekte, Themes und Hotkeys sind in externen JSON-Dateien definiert — keine Code-Änderungen für Regelanpassungen nötig.
- **SQLite-Backend:** `DatabaseManager` (Singleton) indexiert die gesamte Bibliothek in einer lokalen SQLite-Datenbank mit FTS5-Volltextsuche. Automatische Schema-Migration bei Datenbankupdates.
- **Atomares Speichern:** `SaveManager` schreibt Spielstände über eine `.tmp`-Datei (dann Rename), sodass ein Absturz während des Speicherns nie zu einer kaputten Save-Datei führt. Das Format enthält eine Versionskennung für Vorwärtskompatibilität.
- **Snapshot-basiertes Undo/Redo:** `HistoryManager` speichert Deep-Copies des Engine-Zustands vor jeder Mutation. `MAX_HISTORY` in `src/config/__init__.py` konfigurierbar.

### Tests ausführen

```bash
# Alle Tests
pytest

# Einzelne Datei
pytest tests/unit/core/test_engine.py

# Mit Coverage
pytest --cov=src
```

Tests spiegeln die `src/`-Struktur unter `tests/` wider. Mocks für Engine und View befinden sich in `tests/unit/mocks.py`. Integrationstests (keine Mocks) in `tests/integration/`.

---

## ⚖️ Lizenz

Dieses Projekt steht unter der **MIT Lizenz**.
Du darfst den Code frei verwenden, verändern und verbreiten, solange der ursprüngliche Urheberrechtsvermerk erhalten bleibt.