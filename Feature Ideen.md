# Feature Roadmap

---

## 🔧 Offene TODOs (Klein / Bugfix-Nah)

- [ ] **Autosave auf DM-Notizen ausweiten** — DM-Notizen in den normalen Save-/Autosave-Zyklus aufnehmen.
- [ ] **Suche testen & optimieren**
  - Navigation zwischen Treffern (↑/↓)
  - Versionierung des Such-Index prüfen

---

## ⚔️ Kampf-Komfort

- [ ] **Charakter duplizieren**
    - *Warum:* Ein Klick erstellt eine Kopie eines Gegners mit allen Werten. Unverzichtbar wenn mehrere gleiche Gegner im Kampf sind.

- [ ] **Resistenzen & Immunitäten pro Charakter**
    - *Warum:* Schadenstyp-Resistenz (halber Schaden) oder Immunität direkt am Charakter hinterlegen. `calculate_damage()` wertet das automatisch aus.

- [ ] **Gruppen-Initiative**
    - *Warum:* Alle Gegner einer Gruppe würfeln gemeinsam (ein Initiativewert für alle). Standard in vielen PnP-Systemen, spart Zeit bei großen Encounters.

- [ ] **Timer / Countdown**
    - *Warum:* Sichtbarer Countdown für zeitkritische Szenen (z.B. "Falle löst in X Runden aus"). Tickt automatisch mit `next_turn()`.

- [ ] **Kampf-Statistik**
    - *Warum:* Dialog nach "Kampf beenden" mit Total-Schaden, ausgeteilten Effekten und gefallenen Charakteren als Zusammenfassung.

- [ ] **Kampflog-Export**
    - *Warum:* Log am Ende als `.txt` oder `.html` exportieren, mit Zeitstempel und Rundenmarkierungen. Nützlich für Session-Protokolle.

---

## 🗂️ Charakter & Content

- [ ] **Charakter-Notizen**
    - *Warum:* Freitext-Feld pro Charakter (Tooltip oder Popup) für DM-interne Infos, die nicht in der Bibliothek stehen.

- [ ] **Spieler-Presets** (analog zu Gegner-Presets)
    - *Warum:* Spielercharaktere als wiederverwendbare Presets speichern, um sie schnell in neue Kämpfe zu laden.

---

## 📚 Bibliothek & DM-Werkzeuge

- [ ] **Lesezeichen in der Bibliothek**
    - *Warum:* Häufig genutzte Markdown-/PDF-Seiten favorisieren und als Schnellzugriff-Liste anzeigen.

- [ ] **Zufallstabellen**
    - *Warum:* Würfel-in-Tabelle-Mechanismus für Loot, NPC-Namen, Wetter etc., konfigurierbar als Markdown-Tabellen oder JSON.

- [ ] **Session-Zusammenfassung**
    - *Warum:* Automatisch generierter Notiz-Eintrag nach jeder Session (Datum, Runden, Charaktere, Kampflog-Kurzfassung).

---

## 🎨 Polish & Atmosphäre

- [ ] **Soundeffekte für Events** (Tod, Kampfende, Rundenwechsel)
    - *Warum:* Erhöht den Spaßfaktor und gibt akustisches Feedback zu wichtigen Ereignissen.

- [ ] **Separate Spieler-Ansicht (Second Screen)**
    - *Warum:* Initiative und sichtbare HP auf einem zweiten Monitor teilen, ohne Spoiler (DM-Werte, Notizen) zu zeigen.

---

## 🏗️ Langfristig / Architektur

- [ ] **Kampagnen-Verwaltung**
    - *Warum:* Mehrere Kampagnen mit je eigenen Saves, DM-Notizen und Bibliothek-Indizes. Kampagne beim Start auswählen.

- [ ] **Packaging (.exe / Installer)**
    - *Warum:* Einfachere Weitergabe und Installation für Endnutzer ohne Python-Kenntnisse.

---

## ✅ Erledigt

- [x] **Autosave / Kampfprotokoll wiederherstellen** — Letzte Runden des Kampfprotokolls werden mit dem Autosave gespeichert und beim Laden wiederhergestellt.
- [x] **Encounter Generator** — Zufällige Gegnerauswahl filterbar nach Kategorie, Typ und Level-Range. (`_generate_encounter()` in `LibraryImportTab`)
- [x] **Gegner/NPC direkt aus der Bibliothek hinzufügen** — `LibraryImportTab` mit Suche, SQL-Filter und Direkt-Import in den laufenden Kampf.
- [x] **Datenbank-Integration (SQLite)** — `DatabaseManager` mit FTS5-Volltext-Suche und automatischer Schema-Migration.