# Combat Tracker PnP

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-green)

Ein leistungsstarkes und benutzerfreundliches Tool zur Verwaltung von Kämpfen in Pen & Paper Rollenspielen. Entwickelt in Python mit Tkinter, bietet dieser Tracker eine moderne Dark-Mode-Oberfläche und umfassende Funktionen, um Spielleiter (GMs) bei der Kampfführung zu unterstützen.

## 🌟 Features

*   **Charakter-Management**: Einfaches Hinzufügen, Bearbeiten und Entfernen von Spielern und Gegnern.
*   **Initiative-System**: Automatisches Würfeln und Sortieren der Initiative basierend auf Charakterwerten (GEW).
*   **Kampfablauf-Steuerung**: Runden- und Zugverwaltung, "Nächster Zug"-Logik, Überspringen von Zügen.
*   **Status-Effekte**: Detailliertes System für Statuseffekte mit Dauer (Runden) und Rängen. Automatische Aktualisierung zu Beginn des Zuges.
*   **Schadensberechnung**: Integrierter Schadensrechner mit verschiedenen Schadenstypen und Rängen. Berücksichtigt LP (Lebenspunkte), RP (Rüstungspunkte) und SP (Schildpunkte).
*   **Bibliothek & Import**:
    *   Import von Gegnern aus Excel-Listen (`.xlsx`).
    *   Speichern und Laden von Kampf-Szenarien (JSON).
    *   Integrierte Gegner/ NPC-Bibliothek.
*   **Benutzeroberfläche**:
    *   Modernes Dark Theme.
    *   Visuelle Lebensbalken.
    *   Combat Log für detaillierte Ereignisverfolgung.
    *   Tooltips für schnelle Infos.
*   **Hotkeys**: Anpassbare Tastenkürzel für effiziente Bedienung.
*   **History**: Undo/Redo Funktionalität für Aktionen.
*   **Persistenz**: Autosave und manuelles Speichern des aktuellen Kampfstatus.

## 🛠 Installation

1.  **Repository klonen**:
    ```bash
    git clone https://github.com/yourusername/Combat_Tracker_PnP.git
    cd Combat_Tracker_PnP
    ```

2.  **Abhängigkeiten installieren**:
    Stellen Sie sicher, dass Python installiert ist. Installieren Sie die benötigten Pakete:
    ```bash
    pip install pandas openpyxl
    # Tkinter ist normalerweise in der Standard-Python-Installation enthalten.
    ```

3.  **Starten**:
    Führen Sie das Hauptskript aus:
    ```bash
    python Combat_Tracker.py
    ```

## 🎮 Bedienung & Logik

### Kampfablauf
Der `CombatEngine` Kern verwaltet den Zustand des Kampfes.
1.  **Vorbereitung**: Charaktere hinzufügen oder aus der Bibliothek importieren.
2.  **Initiative**: Klick auf "Initiative würfeln". Das System berechnet die Initiative basierend auf dem GEW-Wert (Geschicklichkeit/Gewandtheit) und sortiert die Liste.
3.  **Kampf**: Mit "Nächster Zug" wird durch die Liste iteriert. Der aktive Charakter wird hervorgehoben.
4.  **Runden**: Wenn alle Charaktere an der Reihe waren, wird der Runden-Zähler erhöht.

### Schadensmodell
Das System unterscheidet zwischen verschiedenen Trefferpunkten:
*   **LP (Lebenspunkte)**: Die eigentliche Gesundheit.
*   **RP (Rüstungspunkte)**: Reduzieren physischen Schaden (je nach Implementierung).
*   **SP (Schildpunkte)**: Absorbieren Schaden vor LP/RP.

Schaden kann Typen und Ränge haben, die die Berechnung beeinflussen (z.B. Durchdringung).

### Status-Effekte
Effekte können Charakteren zugewiesen werden (z.B. "Brennend", "Betäubt").
*   Jeder Effekt hat eine **Dauer** (in Runden) und einen **Rang**.
*   Zu Beginn des Zuges eines Charakters werden dessen Effekte verarbeitet (z.B. Schaden durch "Brennen") und die Dauer verringert.
*   Läuft die Dauer ab, wird der Effekt automatisch entfernt.

## 📂 Projektstruktur

```
Combat_Tracker_PnP/
├── Combat_Tracker.py       # Einstiegspunkt der Anwendung
├── src/                    # Quellcode
│   ├── engine.py           # Kernlogik des Kampfes
│   ├── character.py        # Charakter-Klasse und Attribute
│   ├── gui.py              # Haupt-GUI (Tkinter)
│   ├── mechanics.py        # Spielmechaniken (Schaden, Status)
│   ├── library_handler.py  # Verwaltung der Gegner-Bibliothek
│   ├── import_handler.py   # Import von Excel/JSON
│   ├── persistence.py      # Speichern/Laden
│   └── ...                 # Weitere Hilfsmodule (History, Hotkeys, etc.)
├── enemies.json            # Gespeicherte Gegnerdaten
├── gegnerliste.xlsx        # Excel-Importvorlage
└── ...
```
---
*Erstellt mit ❤️ für PnP-Enthusiasten.*

