# Feature Roadmap
- Autosave/Save auf dm_notes ausweiten
- Autosave/Save soll die letzen 3 Runde oder bestimmte anzahl von einträgen im Kampfprotokoll wiederherstellen.
- Suche nochmal testen/optimieren
  - Navigation zwischen treffern 
  - Versionierung prüfen

## Phase 2: Erweiterte Features & Content (Tiefe)
Diese Features erweitern die Möglichkeiten des Tools und bieten mehr Komfort für den Spielleiter.

- **Zufällige Gegnerauswahl (Encounter Generator)**
    - *Warum:* Großes Feature für Spielleiter-Komfort bei spontanen Kämpfen. Filterbar nach Kategorie, Schwierigkeit und Level.
- **Regelwerk Markdowns Format optimieren**
    - *Warum:* Bessere Lesbarkeit und Strukturierung der integrierten Regeln.

## Phase 3: Polish & "Juice" (Atmosphäre)
Features, die das Tool "lebendiger" machen und die User Experience abrunden.

- **Soundeffekte für Events** (Spielertod, NPC-Tod, Gegnertod, Kampfende)
    - *Warum:* Erhöht den Spaßfaktor und gibt akustisches Feedback.
- **Separate Spieler-Ansicht (Second Screen)**
    - *Warum:* Ermöglicht das Teilen von Infos (Initiative, sichtbare HP) auf einem zweiten Monitor, ohne Spoiler (Werte, Notizen) zu zeigen.

## Langfristig / Architektur
- **Datenbank-Integration (SQLite)**
    - *Warum:* Performance bei sehr vielen Daten, bessere Suchmöglichkeiten, Verknüpfung von IDs.
- **Gegner/NPC direkt aus der Bibliothek hinzufügen**
  - *Warum:* Massiver Workflow-Gewinn. Verhindert unnötiges Hin- und Herwechseln zwischen Tabs.
- **Packaging (.exe / Installer)**
    - *Warum:* Einfachere Weitergabe und Installation für Endnutzer.


## Bugs und Fehler

#-----------------------------------------------------------------------------------------------------------------------

4. Verbleibende Verbesserungsvorschläge (Advanced)
Nachdem die kritischen Punkte behoben sind, hier einige Vorschläge für die nächste Stufe der Professionalisierung:
A. Dependency Injection (DI) & Inversion of Control (IoC)
•
Beobachtung: Klassen erstellen oft noch ihre eigenen Abhängigkeiten. Zum Beispiel erzeugt der CombatEngine seinen TurnManager. Die Controller (CombatActionHandler etc.) werden in der CombatTracker-Klasse (der "App") erstellt.
•
Vorschlag: Führe das Prinzip der "Dependency Injection" konsequenter ein. Anstatt dass eine Klasse ihre Helfer selbst erstellt, sollten diese von außen in den Konstruktor "injiziert" werden.
◦
Ein zentraler Ort (z.B. die main-Funktion in Combat_Tracker.py) sollte alle Kern-Objekte instanziieren (Engine, TurnManager, HistoryManager, MainView, alle Handler) und sie dann an die jeweiligen Konstruktoren übergeben.
•
Vorteil:
◦
Testbarkeit: Das Mocking in Tests wird trivial. Man übergibt einfach einen MagicMock an den Konstruktor, statt patch verwenden zu müssen.
◦
Flexibilität: Man könnte leicht einen AdvancedTurnManager statt des normalen TurnManager verwenden, ohne die CombatEngine ändern zu müssen.
◦
Klarheit: Die Abhängigkeiten einer Klasse sind sofort in der __init__-Signatur ersichtlich.
B. Striktere Trennung zwischen UI und Controllern
•
Beobachtung: Die Controller greifen teilweise noch sehr spezifisch auf die View zu (z.B. view.get_damage_data()). Das ist schon gut über das ICombatView-Interface gelöst, aber die Kopplung ist noch recht eng.
•
Vorschlag (Optional): Man könnte die Interaktion weiter entkoppeln, indem die View bei einer Aktion ein generisches "Event-Objekt" oder ein Dictionary mit den Daten an den Controller sendet, anstatt dass der Controller die View aktiv nach Daten fragt.
◦
Beispiel: Der deal_damage-Button in der UI sammelt die Daten und ruft controller.deal_damage(damage_info={'amount': 10, 'type': 'Feuer'}) auf.
•
Vorteil: Der Controller wird noch unabhängiger von der konkreten UI-Implementierung. Dies ist jedoch bereits ein sehr hohes Niveau der Entkopplung und für dieses Projekt eventuell "Over-Engineering". Der aktuelle Zustand ist bereits ein guter Kompromiss.