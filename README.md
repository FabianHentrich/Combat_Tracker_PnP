# ⚔️ PnP Combat Tracker

> ⚠️ **Spoiler-Warnung:**
> In den mitgelieferten Daten befinden sich vollständige Kampagnen, One-Shots und Abenteuer. Wer als Spieler an einer der enthaltenen Kampagnen teilnehmen möchte, sollte die DM-Notizen und die Bibliothek mit Vorsicht genießen! Die Bibliothek lässt sich öffnen ohne das man zwangläufig gespoilert wird. Trotzdem ist es zu empfehlen sich als Spieler nur das Tab _Regelwerk_ anzuschauen.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

Ein professioneller, feature-reicher Combat Tracker für Pen & Paper Rollenspiele, entwickelt mit Python und Tkinter.

> ℹ️ **Hinweis:** Dieses Tool wurde primär für ein **eigenes PnP-Regelwerk** entwickelt.
>
> **Interesse am Regelwerk?** Das Regelwerk und einige Ressourcen aus einer beispielhaften Welt (Orte, Gegner, NPCs, Gegenstände, etc.) sind im Programm einsehbar. Wenn du das näher kennenlernen möchtest oder Fragen hast, schreib mir gerne eine E-Mail!

Dieses Tool unterstützt Spielleiter (Game Masters) dabei, komplexe Kämpfe zu verwalten, Initiative zu tracken, Schaden zu berechnen und Status-Effekte im Blick zu behalten.

---

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Installation & Start](#-installation--start)
- [Benutzung](#-benutzung)
- [Musik-Player](#-musik-player)
- [Programmlogik & Mechaniken](#-programmlogik--mechaniken)
  - [Attribute & Initiative](#runter-attribute--initiative)
  - [Schadensberechnung](#schadensberechnung)
  - [Status-Effekte](#status-effekte)
- [Konfiguration & Anpassung](#-konfiguration--anpassung)
- [Hotkeys](#-hotkeys)
- [Entwickler-Infos](#-entwickler-infos)
- [Lizenz](#-lizenz)

---

## ✨ Features

*   **Responsive UI:** Das Interface passt sich automatisch an verschiedene Bildschirmgrößen und -auflösungen an. Schriftgrößen skalieren dynamisch basierend auf der Bildschirmauflösung.
*   **DM-Notizen & Pläne:** Eigenes Panel für DM-Notizen und Kampagnenplanung (Markdown, Dateibaum, Versionierung, Undo/Redo, Autosave, Drag & Drop, Umbenennen/Löschen, Schnellzugriff auf zuletzt geöffnete Notizen).
*   **Markdown & PDF Bibliothek:** Verwalte dein Wissen in Markdown-Dateien oder zeige PDFs (z.B. Regelwerke) direkt im Tool an.
*   **Volltextsuche:** Durchsuche Markdown-Dateien und PDFs global innerhalb der Anwendung.
*   **Theme-Anpassung:** Alle Panels, Markdown-Viewer, PDF-Viewer und Such-Highlights passen sich dynamisch an das gewählte Farbschema an.
*   **Intelligente Verlinkung:**
    *   Markdown-Links (`[[Link]]`) öffnen direkt die entsprechende Datei.
    *   PDF-Links (`[[rules:123]]`) springen direkt zur angegebenen Seite im Regelwerks-PDF.
*   **Versionierung:** Änderungen an Notizen werden automatisch versioniert (Rückgängig bis zu 20 Versionen, Wert anpassbar in `src/config/__init__.py`).
*   **Drag & Drop:** Markdown-Dateien können direkt ins DM-Notizen-Panel gezogen und hinzugefügt werden.
*   **Schnellzugriff:** Die zuletzt geöffneten Notizen sind als eigene Liste im DM-Notizen-Panel verfügbar.
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
*   **Mehrsprachigkeit:** Die Benutzeroberfläche ist auf Deutsch und Englisch verfügbar. Die Sprache kann jederzeit über das Menü gewechselt werden, ohne den Kampfzustand zu verlieren.
*   **Absturzerkennung:** Beim Start erkennt das Programm automatisch einen vorherigen Absturz (via Lock-File) und bietet an, den letzten Autosave wiederherzustellen.

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
3.  Erstelle und aktiviere eine virtuelle Umgebung (empfohlen):
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    source .venv/bin/activate
    ```
4.  Installiere die Abhängigkeiten:
    ```bash
    pip install -r requirements.txt
    ```
5.  Starte das Programm:
    ```bash
    python Combat_Tracker.py
    ```

---

## 🎮 Benutzung

Das Hauptfenster ist in intuitiv bedienbare Bereiche unterteilt:
1.  **DM-Notizen (linkes Panel):** Eigenes Panel für Kampagnenplanung und Session-Vorbereitung. Unterstützt Markdown, Dateibaum, Undo/Redo und Drag & Drop.
2.  **Initiative-Liste:** Zeigt alle Charaktere in der aktuellen Reihenfolge. Der aktive Charakter ist hervorgehoben.
    *   **Charakter bearbeiten:** Doppelklick auf einen Charakter öffnet den Bearbeitungs-Dialog (alle Werte änderbar).
    *   **Charakter löschen:** Charakter auswählen und `Entf` drücken (oder Button im Panel).
3.  **Kontroll-Panel:** Buttons zum Hinzufügen von Charakteren, Würfeln der Initiative und Steuern des Rundenablaufs ("Nächster Zug").
4.  **Interaktions-Panel:** Hier werden Aktionen auf die *aktuell ausgewählten* Charaktere angewendet.
    *   **Mehrfachauswahl:** Halte `Strg` oder `Shift` gedrückt, um mehrere Charaktere in der Liste auszuwählen. Aktionen werden auf alle angewendet.
    *   **Dynamische Zeilen:** Füge über den `+` Button weitere Schadenskomponenten hinzu (z.B. 10 Feuer und 5 Kälte).
    *   **Status:** Wähle Status-Effekte, Rang und Dauer.
5.  **Bibliothek:** Zugriff auf die integrierte Wiki und Gegner-Presets. Enthält die Tabs: *Regelwerk, Gegenstände, Gegner (Info), NPCs, Orte, Organisationen, Götter*.
6.  **Log:** Ein detailliertes Protokoll aller Ereignisse (Schaden, Rundenwechsel, Effekte).

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

### <a id="runter-attribute--initiative"></a>Attribute & Initiative
Jeder Charakter verfügt über folgende Kern-Werte:
*   **LP (Lebenspunkte):** Die Gesundheit des Charakters. Sinkt diese auf 0, gilt der Charakter als kampfunfähig.
*   **RP (Rüstungspunkte):** Physische Rüstung. Kann Schaden absorbieren, nutzt sich dabei aber ab.
*   **SP (Schildpunkte):** Ein energetischer oder magischer Schild. Regeneriert sich in der Regel nicht automatisch, absorbiert aber Schaden vor der Rüstung.
*   **GEW (Gewandtheit):** Bestimmt den Würfel für die Initiative.

**Initiative-Berechnung:**
Die Initiative wird basierend auf dem GEW-Wert gewürfelt. Dabei kommt ein **"Exploding Dice"** (explodierender Würfel) System zum Einsatz: Würfelt man die höchstmögliche Augenzahl, darf man erneut würfeln und das Ergebnis addieren.

| Charakter-Wert | Würfel |
|:---------------| :--- |
| 1              | W4 |
| 2              | W6 |
| 3              | W8 |
| 4              | W10 |
| 5              | W12 |
| 6+             | W20 |

### Schadensberechnung
Wenn ein Charakter Schaden erleidet, prüft das System den **Schadenstyp** und wendet folgende Prioritätenkette an:

1.  **Normaler Schaden (Waffenschaden, Feuer, Kälte, Blitz, Verwesung, Gift):**
    *   **Phase 1 - Schild:** Der Schaden trifft zuerst den Schild (SP). Solange SP > 0 sind, wird Schaden 1:1 absorbiert.
    *   **Phase 2 - Rüstung:** Verbleibender Schaden trifft die Rüstung (RP).
        *   Die Rüstung absorbiert Schaden bis zur Höhe von `RP * 2`.
        *   **Abnutzung:** Die Rüstung verliert dabei an Haltbarkeit.
            *   Die Rüstung verliert RP in Höhe der **Hälfte des absorbierten Schadens** (aufgerundet).
            *   *Formel:* `Verlorene RP = (Absorbierter Schaden + 1) / 2` (Ganzzahl-Division)
    *   **Phase 3 - Leben:** Alles, was Schild und Rüstung nicht abfangen konnten, wird von den Lebenspunkten (LP) abgezogen.

2.  **Durchdringend (Durchschlagsschaden):**
    *   Ignoriert die **Rüstung (RP)** komplett.
    *   Wird aber noch vom **Schild (SP)** reduziert.
    *   Ideal gegen schwer gepanzerte Ziele ohne Energieschild.

3.  **Direkt (Direktschaden):**
    *   Ignoriert **Schild (SP)** UND **Rüstung (RP)**.
    *   Geht direkt auf die Lebenspunkte (LP).
    *   Sehr gefährlich, da keine passive Verteidigung hilft.

**Zusatzeffekte:**
Bestimmte Schadenstypen (Elementarschaden) haben eine Chance, Statuseffekte auszulösen (abhängig vom Rang der Fähigkeit):
*   **Feuer:** Kann *Verbrennung* auslösen.
*   **Blitz:** Kann *Betäubung* auslösen.
*   **Kälte:** Kann *Unterkühlung* auslösen.
*   **Gift:** Kann *Vergiftung* auslösen.
*   **Verwesung:** Kann *Erosion* auslösen.

### Status-Effekte
Effekte werden automatisch verwaltet und lösen meist zu Beginn des Zuges eines Charakters aus. Jeder Effekt hat eine **Dauer** (in Runden) und einen **Rang** (Stärke 1-6).

*   **☠️ Vergiftung (Poison):** Verursacht pro Runde `Rang` Punkte **Direktschaden**.
*   **🔥 Verbrennung (Burn):** Verursacht pro Runde `Rang` Punkte **Normalen Schaden**.
*   **🩸 Blutung (Bleed):** Verursacht **Normalen Schaden**, der mit der Zeit schlimmer wird (`Rang / 2 + Runden - 1`).
*   **🧪 Erosion:**
    *   Verursacht dauerhaften Verlust von `Rang * W4` **Maximalen LP**.
    *   Verursacht zusätzlich den gleichen Betrag als **Direktschaden**.
*   **❄️ Unterkühlung (Freeze):** Der Charakter verliert seine **Bonusaktion** für `Rang` Runden.
*   **⚡ Betäubung (Stun):** Der Charakter verliert **alle Aktionen** für 1 Runde.
*   **🥵 Erschöpfung (Exhaustion):** Malus von **-2 auf GEWANDTHEIT** für 1 Runde.
*   **🤪 Verwirrung (Confusion):** Malus von **-1 auf Kampf-Proben** für 1 Runde.
*   **🙈 Blendung (Blind):** Malus auf Aktionen/Angriffe (abhängig vom Rang, z.B. -1 bis -3).
*   **⚔️ Entwaffnet (Disarmed):** Die aktuell geführte Waffe kann nicht eingesetzt werden.
*   **💚 Heilung (Regeneration):** Stellt zu Beginn des Zuges Lebenspunkte wieder her (Höhe entspricht Rang).

*Hinweis: Wenn ein Charakter bereits einen Effekt hat und denselben Effekt erneut erhält, wird oft die Dauer verlängert oder der Rang erhöht (je nach Konfiguration).*

---

## ⚙️ Konfiguration & Anpassung

Das Programm ist hochgradig anpassbar über JSON-Dateien im `data/` Verzeichnis:

*   **`data/i18n/*_rules.json` (Dynamisches Regelwerk):** Das Herzstück der Anpassbarkeit. Hier können Schadensarten, ihre Effekte (z.B. `ignores_armor`) und Status-Effekte (inkl. `max_rank`, `stackable`) frei definiert oder geändert werden, ohne den Code anzufassen.
*   **`data/enemies.json`**: Eine Bibliothek deiner häufigsten Gegner (Presets).
*   **`data/hotkeys.json`**: Anpassbare Tastenkürzel.
*   **`data/` Unterordner**: Markdown-Dateien für die Bibliothek (Regeln, Items, NPCs, Orte, etc.).
*   **`src/config/__init__.py` (Source)**: Hier können Themes und Schriftarten angepasst werden.

### Themes
Über das Menü oder die Config können verschiedene Themes gewählt werden:

| Dark Themes | Light Themes |
| :--- | :--- |
| `Neutral Dark` | `Neutral Light` |
| `Gruvbox Dark` | `Gruvbox Light` |
| `Nord Dark` (Standard) | `Nord Light` |
| `Monokai Dark` | `Solarized Light` |

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
| **Musik Play/Pause** | `Strg + P` |
| **Nächster Titel** | `Strg + →` |
| **Vorheriger Titel** | `Strg + ←` |
| **Lautstärke +** | `Strg + ↑` |
| **Lautstärke -** | `Strg + ↓` |
| **Stummschalten** | `Strg + M` |

*(Hotkeys können in `data/hotkeys.json` angepasst werden)*

---

## 🛠️ Entwickler-Infos

Für Entwickler, die am Code arbeiten möchten, wurde die Architektur modernisiert und modularisiert.

### Projektstruktur
Der Code ist nun sauber in Module unterteilt (`src/`):
*   **`src/core/`**: Enthält die reine Business-Logik (Engine, Mechaniken, History). Unabhängig von der UI.
*   **`src/models/`**: Datenmodelle (Character, StatusEffects, Enums).
*   **`src/controllers/`**: Handler für Import, Export, Hotkeys, Persistenz und die Bibliothek.
*   **`src/ui/`**: Die grafische Oberfläche (Tkinter), getrennt von der Logik.
*   **`src/config/`**: Zentrale Konfiguration (Themes, Schriftarten, Konstanten).
*   **`src/utils/`**: Hilfsfunktionen, Logger und Konfiguration.
*   **`data/`**: Enthält JSON-Konfigurationsdateien und die Markdown-Bibliothek.
*   **`saves/`**: Speicherort für Spielstände und Autosaves.
*   **`logs/`**: Protokolle aller Ereignisse und Fehler (z.B. combat_tracker.log).
*   **`tests/`**: Unit- und Integrationstests mit `pytest`.

### Tests ausführen
Um die Tests auszuführen, verwende:
```bash
pytest
```

### Architektur-Highlights
*   **Composition Root / Manuelles Dependency Injection:** `MainWindow` fungiert als Composition Root — alle Abhängigkeiten (Engine, Handler, Controller) werden dort instanziiert und manuell verdrahtet, ohne Framework.
*   **MVC-Ansatz:** Striktere Trennung von Daten (Models), Logik (Core) und Anzeige (UI).
*   **UUIDs:** Charaktere werden intern über eindeutige IDs identifiziert, um Namenskonflikte zu vermeiden.
*   **Event-System:** Die UI reagiert auf Events der Engine, statt direkt Daten zu manipulieren.
*   **Datengetriebenes Design:** Spielregeln, Themes und Hotkeys sind in externen JSON-Dateien definiert und können ohne Code-Änderungen angepasst werden.

---

## ⚖️ Lizenz

Dieses Projekt steht unter der **MIT Lizenz**.
Das bedeutet, du darfst den Code frei verwenden, verändern und verbreiten, solange der ursprüngliche Urheberrechtsvermerk erhalten bleibt.
