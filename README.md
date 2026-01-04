# ⚔️ PnP Combat Tracker

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

Ein professioneller, feature-reicher Combat Tracker für Pen & Paper Rollenspiele.

> ℹ️ **Hinweis:** Dieses Tool wurde primär für ein **eigenes PnP-Regelwerk** entwickelt.
>
> **Interesse am Regelwerk?** Das Regelwerk und einige Ressourcen aus der einer beispielhaften Welt (Orte, Gegner, NPCs, Gegenstände, etc.) sind im Programm einsehbar. Wenn du das näher kennenlernen möchtest oder Fragen hast, schreib mir gerne eine E-Mail!

Dieses Tool unterstützt Spielleiter (Game Masters) dabei, komplexe Kämpfe zu verwalten, Initiative zu tracken, Schaden zu berechnen und Status-Effekte im Blick zu behalten.

---

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Installation & Start](#-installation--start)
- [Benutzung](#-benutzung)
- [Musik-Player](#-musik-player)
- [Programmlogik & Mechaniken](#-programmlogik--mechaniken)
  - [Attribute](#attribute)
  - [Schadensberechnung](#schadensberechnung)
  - [Status-Effekte](#status-effekte)
- [Konfiguration & Anpassung](#-konfiguration--anpassung)
- [Hotkeys](#-hotkeys)
- [Lizenz](#-lizenz)

---

## ✨ Features

*   **Initiative-Verwaltung:** Automatisches Würfeln und Sortieren der Initiative basierend auf dem Gewandtheits-Wert (GEW).
*   **Erweitertes Schadenssystem:** Unterscheidung zwischen Lebenspunkten (LP), Rüstungspunkten (RP) und Schildpunkten (SP).
*   **Dynamische Schadenseingabe:** Kombiniere mehrere Schadensarten in einer Aktion (z.B. "10 Feuer + 5 Kälte").
*   **Mehrfachauswahl:** Wende Aktionen wie Schaden oder Heilung auf mehrere Charaktere gleichzeitig an (`Strg+Klick` oder `Shift+Klick`).
*   **Schadenstypen:** Verschiedene Schadensarten (z.B. Normal, Durchdringend, Direkt, Elementar) mit unterschiedlichen Auswirkungen auf Rüstung und Schilde.
*   **Status-Effekte:** Umfassendes System für Zustände (Gift, Brand, Betäubung, etc.) mit automatischer Rundenverwaltung, Rängen und Stapelbarkeit.
*   **Charakter-Management:** Einfaches Hinzufügen von Spielern, Gegnern und NPCs. Speichern und Laden von Gegner-Listen.
*   **Integrierte Bibliothek / Wiki:** Verwalte deine gesamte Kampagne direkt im Tool. Durchsuche Regeln, Items, NPCs, Orte und mehr in einer übersichtlichen Markdown-basierten Bibliothek.
*   **Excel Import:** Importiere Charaktere und Gegner direkt aus Excel-Tabellen (.xlsx), um Vorbereitungszeit zu sparen.
*   **Musik-Player:** Integrierter Audio-Player für lokale Dateien mit Playlist- und Loop-Funktionen.
*   **Dice Roller:** Integrierter Würfel-Simulator für gängige PnP-Würfel (W4 bis W100).
*   **Themes:** Wähle aus verschiedenen Farbschemata (Nord, Gruvbox, Monokai, etc.). Vollständige Unterstützung für Light- und Dark-Modes über alle UI-Elemente hinweg.
*   **Persistenz & Autosave:** Der Kampfzustand wird **nach jeder Änderung** (Schaden, Zugwechsel, etc.) automatisch in `saves/autosave.json` gespeichert. Bei einem Absturz kann diese Datei einfach über "Kampf laden..." wiederhergestellt werden.
*   **Undo/Redo:** Fehler können einfach rückgängig gemacht werden.

---

## 🚀 Installation & Start

### Voraussetzungen
*   Python 3.8 oder höher
*   Abhängigkeiten aus `requirements.txt`
    *   **Windows/macOS:** `tkinter` ist meist im Python-Installer enthalten.
    *   **Linux:** Muss oft separat installiert werden: `sudo apt-get install python3-tk`

### Starten
1.  Klone das Repository:
    ```bash
    git clone https://github.com/DeinUsername/Combat_Tracker_PnP.git
    ```
2.  Navigiere in das Verzeichnis:
    ```bash
    cd Combat_Tracker_PnP
    ```
3.  Installiere die Abhängigkeiten:
    ```bash
    pip install -r requirements.txt
    ```
4.  Starte das Programm:
    ```bash
    python Combat_Tracker.py
    ```

---

## 🎮 Benutzung

Das Hauptfenster ist in intuitiv bedienbare Bereiche unterteilt:
1.  **Initiative-Liste:** Zeigt alle Charaktere in der aktuellen Reihenfolge. Der aktive Charakter ist hervorgehoben.
2.  **Kontroll-Panel:** Buttons zum Hinzufügen von Charakteren, Würfeln der Initiative und Steuern des Rundenablaufs ("Nächster Zug").
3.  **Interaktions-Panel:** Hier werden Aktionen auf die *aktuell ausgewählten* Charaktere angewendet.
    *   **Mehrfachauswahl:** Halte `Strg` oder `Shift` gedrückt, um mehrere Charaktere in der Liste auszuwählen. Aktionen werden auf alle angewendet.
    *   **Dynamische Zeilen:** Füge über den `+` Button weitere Schadenskomponenten hinzu (z.B. 10 Feuer und 5 Kälte).
    *   **Status:** Wähle Status-Effekte, Rang und Dauer.
4.  **Bibliothek:** Zugriff auf die integrierte Wiki und Gegner-Presets.
5.  **Log:** Ein detailliertes Protokoll aller Ereignisse (Schaden, Rundenwechsel, Effekte).

---

## 🎵 Musik-Player

Der integrierte Musik-Player ermöglicht es, die passende Atmosphäre für jede Szene zu schaffen. Er befindet sich oben rechts über dem Interaktions-Panel.

*   **Lokale Wiedergabe:** Spiele Musikdateien (MP3, WAV, OGG) direkt von deinem Computer ab.
*   **Playlist-Management:** Öffne die Musikeinstellungen (Zahnrad-Symbol), um Dateien hinzuzufügen. Du kannst Titel per Drag & Drop sortieren.
*   **Loop-Modi:**
    *   🔁 **Einzeln (Inf):** Wiederholt den aktuellen Titel unendlich.
    *   🔢 **Anzahl (x N):** Wiederholt einen Titel N-mal, bevor zum nächsten gewechselt wird.
    *   🔄 **Playlist:** Wenn kein Loop aktiv ist, wird die Playlist von oben nach unten abgespielt.
*   **Tabletop Audio:** Ein Button öffnet [Tabletop Audio](https://tabletopaudio.com/) im Browser, um dort Sounds abzuspielen.
*   **Steuerung:** Play/Pause, Vor/Zurück, Lautstärke und Mute sind direkt im Hauptfenster erreichbar.

---

## 🧠 Programmlogik & Mechaniken

Das Herzstück des Trackers ist die automatische Berechnung von Kampfereignissen. Hier wird detailliert erklärt, wie das Programm "denkt" und welche Regeln angewendet werden.

### Attribute & Initiative
Jeder Charakter verfügt über folgende Kern-Werte:
*   **LP (Lebenspunkte):** Die Gesundheit des Charakters. Sinkt diese auf 0, gilt der Charakter als kampfunfähig.
*   **RP (Rüstungspunkte):** Physische Rüstung. Kann Schaden absorbieren, nutzt sich dabei aber ab.
*   **SP (Schildpunkte):** Ein energetischer oder magischer Schild. Regeneriert sich in der Regel nicht automatisch, absorbiert aber Schaden vor der Rüstung.
*   **GEW (Gewandtheit):** Bestimmt den Würfel für die Initiative.

**Initiative-Berechnung:**
Die Initiative wird basierend auf dem GEW-Wert gewürfelt. Dabei kommt ein **"Exploding Dice"** (explodierender Würfel) System zum Einsatz: Würfelt man die höchstmögliche Augenzahl, darf man erneut würfeln und das Ergebnis addieren.

| GEW Wert | Würfel |
| :--- | :--- |
| 1 | W4 |
| 2 | W6 |
| 3 | W8 |
| 4 | W10 |
| 5 | W12 |
| 6+ | W20 |

### Schadensberechnung
Wenn ein Charakter Schaden erleidet, prüft das System den **Schadenstyp** und wendet folgende Prioritätenkette an:

1.  **Normaler Schaden (Normal, Feuer, Kälte, Blitz, Verwesung):**
    *   **Phase 1 - Schild:** Der Schaden trifft zuerst den Schild (SP). Solange SP > 0 sind, wird Schaden 1:1 absorbiert.
    *   **Phase 2 - Rüstung:** Verbleibender Schaden trifft die Rüstung (RP).
        *   Die Rüstung absorbiert Schaden bis zur Höhe von `RP * 2`.
        *   **Abnutzung:** Die Rüstung verliert dabei an Haltbarkeit.
            *   Die Rüstung verliert RP in Höhe der **Hälfte des absorbierten Schadens** (aufgerundet).
            *   *Formel:* `Verlorene RP = (Absorbierter Schaden + 1) / 2` (Ganzzahl-Division)
    *   **Phase 3 - Leben:** Alles, was Schild und Rüstung nicht abfangen konnten, wird von den Lebenspunkten (LP) abgezogen.

2.  **Durchdringend:**
    *   Ignoriert die **Rüstung (RP)** komplett.
    *   Wird aber noch vom **Schild (SP)** reduziert.
    *   Ideal gegen schwer gepanzerte Ziele ohne Energieschild.

3.  **Direkt (Direkt, Gift, Erosion):**
    *   Ignoriert **Schild (SP)** UND **Rüstung (RP)**.
    *   Geht direkt auf die Lebenspunkte (LP).
    *   Sehr gefährlich, da keine passive Verteidigung hilft.

### Status-Effekte
Effekte werden automatisch verwaltet und lösen meist zu Beginn des Zuges eines Charakters aus. Jeder Effekt hat eine **Dauer** (in Runden) und einen **Rang** (Stärke 1-6).

*   **☠️ Vergiftung (Poison):** Verursacht pro Runde `Rang` Punkte **Direktschaden** (ignoriert Rüstung/Schild).
*   **🔥 Verbrennung (Burn):** Verursacht pro Runde `Rang` Punkte **Normalen Schaden** (wird von Rüstung/Schild reduziert).
*   **🩸 Blutung (Bleed):** Verursacht **Normalen Schaden**, der mit der Zeit schlimmer wird.
    *   Formel: `Schaden = (Rang / 2) + (Runden aktiv - 1)`.
*   **🧪 Erosion:** Zersetzt den Körper dauerhaft.
    *   Verursacht `Rang * W4` Schaden an den **Maximalen LP**. Dieser Schaden ist im Kampf nicht rückgängig zu machen.
    *   Verursacht zusätzlich den gleichen Betrag als **Direktschaden**.
*   **❄️ Unterkühlung (Freeze):** Der Charakter verliert seine Bonusaktion (wird im Log angezeigt).
*   **⚡ Betäubung (Stun):** Der Charakter verliert seine Aktion.

*Hinweis: Wenn ein Charakter bereits einen Effekt hat und denselben Effekt erneut erhält, wird oft die Dauer verlängert oder der Rang erhöht (je nach Konfiguration).*

---

## ⚙️ Konfiguration & Anpassung

Das Programm ist hochgradig anpassbar über JSON-Dateien im `data/` Verzeichnis:

*   **`data/rules.json` (Dynamisches Regelwerk):** Das Herzstück der Anpassbarkeit. Hier können Schadensarten, ihre Effekte (z.B. `ignores_armor`) und Status-Effekte (inkl. `max_rank`, `stackable`) frei definiert oder geändert werden, ohne den Code anzufassen.
*   **`data/enemies.json`**: Eine Bibliothek deiner häufigsten Gegner (Presets).
*   **`data/hotkeys.json`**: Anpassbare Tastenkürzel.
*   **`data/` Unterordner**: Markdown-Dateien für die Bibliothek (Regeln, Items, NPCs, Orte, etc.).
*   **`src/config/__init__.py` (Source)**: Hier können Themes und Schriftarten angepasst werden.

### Themes
Über das Menü oder die Config können verschiedene Themes gewählt werden, z.B.:
*   `Nord Dark` (Standard)
*   `Gruvbox`
*   `Monokai`
*   `Solarized Light`

---

## ⌨️ Hotkeys

Für einen schnellen Workflow während des Spiels:

| Aktion | Hotkey (Default) |
| :--- | :--- |
| **Nächster Zug** | `<Leertaste>` |
| **Rückgängig (Undo)** | `Strg + Z` |
| **Wiederholen (Redo)** | `Strg + Y` |
| **Charakter löschen** | `Entf` |
| **Fokus auf Schaden** | `Strg + D` |

*(Hotkeys können in `data/hotkeys.json` angepasst werden)*

---

## 🛠️ Entwickler-Infos

Für Entwickler, die am Code arbeiten möchten, wurde die Architektur modernisiert und modularisiert.

### Projektstruktur
Der Code ist nun sauber in Module unterteilt (`src/`):
*   **`src/core/`**: Enthält die reine Business-Logik (Engine, Mechaniken, History). Unabhängig von der UI.
*   **`src.models/`**: Datenmodelle (Character, StatusEffects).
*   **`src/controllers/`**: Handler für Import, Export, Hotkeys, Persistenz und die Bibliothek.
*   **`src.ui/`**: Die grafische Oberfläche (Tkinter), getrennt von der Logik.
*   **`src/utils/`**: Hilfsfunktionen, Logger und Konfiguration.
*   **`data/`**: Enthält JSON-Konfigurationsdateien und die Markdown-Bibliothek.
*   **`saves/`**: Speicherort für Spielstände und Autosaves.

### Architektur-Highlights
*   **MVC-Ansatz:** Striktere Trennung von Daten (Models), Logik (Core) und Anzeige (UI).
*   **UUIDs:** Charaktere werden intern über eindeutige IDs identifiziert, um Namenskonflikte zu vermeiden.
*   **Event-System:** Die UI reagiert auf Events der Engine, statt direkt Daten zu manipulieren.

---

## ⚖️ Lizenz

Dieses Projekt steht unter der **MIT Lizenz**.
Das bedeutet, du darfst den Code frei verwenden, verändern und verbreiten, solange der ursprüngliche Urheberrechtsvermerk erhalten bleibt.
