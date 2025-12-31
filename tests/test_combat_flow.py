import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.character import Character
from src.enums import EventType

@pytest.fixture(scope="function")
def app():
    """Fixture für die CombatTracker App mit gemockter UI."""
    with patch.dict(sys.modules, {
        'tkinter': MagicMock(),
        'tkinter.ttk': MagicMock(),
        'tkinter.filedialog': MagicMock(),
        'tkinter.messagebox': MagicMock()
    }):
        # Import or reload src.main_window to use the mocked tkinter
        if 'src.dice_roller' in sys.modules:
            importlib.reload(sys.modules['src.dice_roller'])
        if 'src.ui_layout' in sys.modules:
            importlib.reload(sys.modules['src.ui_layout'])
        if 'src.main_window' in sys.modules:
            importlib.reload(sys.modules['src.main_window'])
        else:
            import src.main_window

        CombatTracker = sys.modules['src.main_window'].CombatTracker

        root = MagicMock()
        tracker = CombatTracker(root)

        # Mocke interne UI-Komponenten, auf die zugegriffen wird
        tracker.tree = MagicMock()
        tracker.log = MagicMock()
        tracker.round_label = MagicMock()

        # Leere die Charakterliste für jeden Test
        tracker.engine.characters = []
        tracker.engine.turn_index = -1
        tracker.engine.round_number = 1
        tracker.initiative_rolled = False

        yield tracker

def test_add_character(app):
    """
    Testet das Hinzufügen eines Charakters zur Engine über die App-Methode.
    Überprüft, ob der Charakter in der Liste erscheint.
    """
    c = Character("Hero", 10, 10, 10, 10, char_type="Spieler")
    app.insert_character(c)
    assert c in app.engine.characters
    assert len(app.engine.characters) == 1

def test_initiative_sorting(app):
    """
    Testet die Sortierung der Initiative.
    Charaktere mit höherer Initiative sollten zuerst kommen.
    """
    c1 = Character("Slow", 10, 10, 10, 5, char_type="Gegner")
    c2 = Character("Fast", 10, 10, 10, 20, char_type="Spieler")
    app.engine.characters = [c1, c2]

    app.roll_initiative_all()

    # Fast (Init 20) sollte vor Slow (Init 5) sein
    assert app.engine.characters[0] == c2
    assert app.engine.characters[1] == c1

    assert app.initiative_rolled is True
    # Turn Index sollte auf 0 gesetzt sein (erster Char ist dran)
    assert app.engine.turn_index == 0

def test_next_turn_cycle(app):
    """
    Testet den Rundenwechsel und Zugwechsel.
    Überprüft, ob der Turn-Index und die Rundennummer korrekt aktualisiert werden.
    """
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    app.engine.characters = [c1, c2]
    app.initiative_rolled = True
    app.engine.turn_index = 0 # A ist aktiv
    app.engine.round_number = 1

    # A ist fertig -> B ist dran
    app.next_turn()
    assert app.engine.turn_index == 1
    assert app.engine.round_number == 1

    # B ist fertig -> A ist dran (Runde 2)
    app.next_turn()
    assert app.engine.turn_index == 0
    assert app.engine.round_number == 2

def test_surprise_character_insertion(app):
    """
    Testet das Einfügen eines Charakters mit 'surprise=True'.
    Der neue Charakter sollte sofort an der Reihe sein (aktiver Index).
    """
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    app.engine.characters = [c1, c2]
    app.initiative_rolled = True
    app.engine.turn_index = 0 # A ist gerade dran

    # Neuer Charakter C springt rein (surprise=True)
    c3 = Character("C", 10, 10, 10, 15)
    app.insert_character(c3, surprise=True)

    # C sollte jetzt an Position 0 sein (da turn_index 0 war)
    # und A sollte auf Position 1 rutschen.
    # Der aktive Index (turn_index) sollte immer noch auf den "Aktiven" zeigen.
    # Die Logik in insert_character bei surprise ist:
    # target_index = turn_index (0)
    # insert at 0.
    # C ist jetzt an 0. A an 1.
    # turn_index bleibt 0.
    # Also ist C jetzt der aktive Charakter.

    assert app.engine.characters[0] == c3
    assert app.engine.characters[1] == c1
    assert app.engine.turn_index == 0 # C ist aktiv

def test_delete_active_character(app):
    """
    Testet das Löschen des aktuell aktiven Charakters.
    Der Turn-Index sollte so angepasst werden, dass der nächste Charakter dran ist.
    """
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    c3 = Character("C", 10, 10, 10, 5)
    app.engine.characters = [c1, c2, c3]
    app.initiative_rolled = True
    app.engine.turn_index = 1 # B ist dran

    # Mocking der UI-Selektion für Charakter B (Index 1)
    # Wir simulieren, dass der User B in der Tabelle ausgewählt hat
    app.tree.selection.return_value = ["item_id_for_B"]

    # Mock für item() Aufruf mit Option "values"
    def mock_item_b(item, option=None):
        if option == "values":
             return ["2", "B", "Gegner", "10/10", "10/10", "10/10", "10", ""]
        return {}
    app.tree.item.side_effect = mock_item_b

    app.tree.index.return_value = 1

    # Löschen ausführen
    app.delete_character()

    # B sollte weg sein
    assert len(app.engine.characters) == 2
    assert c2 not in app.engine.characters
    assert app.engine.characters[0] == c1
    assert app.engine.characters[1] == c3

    # Da der aktive Char (Index 1) gelöscht wurde, rutscht der nächste (C) auf Index 1.
    # Der turn_index sollte idealerweise auf 1 bleiben (damit C dran ist) oder angepasst werden.
    # In der aktuellen Implementierung:
    # "elif actual_index == self.turn_index: ... if self.turn_index >= len(self.characters): self.turn_index = 0"
    # Index bleibt 1, was jetzt C ist. Das ist korrekt für "der Nächste ist dran".
    assert app.engine.turn_index == 1

def test_delete_previous_character(app):
    """
    Testet das Löschen eines Charakters, der in der Liste VOR dem aktiven Charakter steht.
    Der Turn-Index muss verringert werden, damit der aktive Charakter aktiv bleibt.
    """
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    app.engine.characters = [c1, c2]
    app.initiative_rolled = True
    app.engine.turn_index = 1 # B ist dran

    # Wir löschen A (Index 0)
    app.tree.selection.return_value = ["item_id_for_A"]

    # Mock für item() Aufruf mit Option "values"
    def mock_item_a(item, option=None):
        if option == "values":
             return ["1", "A", "Gegner", "10/10", "10/10", "10/10", "10", ""]
        return {}
    app.tree.item.side_effect = mock_item_a

    app.tree.index.return_value = 0

    app.delete_character()

    # A weg, B rutscht auf 0
    assert app.engine.characters[0] == c2

    # Turn Index muss verringert werden, damit er auf B (jetzt 0) zeigt
    assert app.engine.turn_index == 0

def test_reset_initiative(app):
    """
    Testet das Zurücksetzen der Initiative.
    Überprüft, ob Init-Werte auf 0 gesetzt werden und der Kampfstatus zurückgesetzt wird.
    """
    c1 = Character("A", 10, 10, 10, 20, char_type="Spieler")
    c2 = Character("B", 10, 10, 10, 15, char_type="Gegner")
    app.engine.characters = [c1, c2]
    app.initiative_rolled = True
    app.engine.turn_index = 1

    # Reset nur für Gegner
    app.reset_initiative("Gegner")
    assert c2.init == 0
    assert c1.init == 20 # Spieler bleibt
    assert app.initiative_rolled is False # Modus beendet
    assert app.engine.turn_index == -1

    # Reset Alle
    app.initiative_rolled = True # Wieder an
    app.reset_initiative("All")
    assert c1.init == 0
    assert c2.init == 0

def test_event_subscription_and_notification(app):
    """
    Testet das Event-System der Engine.
    Überprüft, ob Subscriber benachrichtigt werden, wenn ein Event gefeuert wird.
    """
    # Mock Subscriber
    subscriber_mock = MagicMock()

    # Subscribe
    app.engine.subscribe(EventType.UPDATE, subscriber_mock)

    # Notify
    app.engine.notify(EventType.UPDATE)

    # Check if called
    subscriber_mock.assert_called_once()

    # Notify with data
    app.engine.notify(EventType.LOG, "Test Message")
    # Note: The mock was subscribed to UPDATE, not LOG.
    subscriber_mock.assert_called_once() # Should not increase

    # Subscribe to LOG
    app.engine.subscribe(EventType.LOG, subscriber_mock)
    app.engine.notify(EventType.LOG, "Test Message")

    assert subscriber_mock.call_count == 2

def test_next_turn_empty_list(app):
    """
    Testet next_turn bei leerer Charakterliste.
    Sollte keinen Fehler werfen und None zurückgeben.
    """
    app.engine.characters = []
    char = app.engine.next_turn()
    assert char is None

def test_remove_invalid_index(app):
    """
    Testet das Entfernen eines Charakters mit ungültigem Index.
    Sollte abgefangen werden (kein Crash).
    """
    c1 = Character("A", 10, 10, 10, 10)
    app.engine.characters = [c1]

    # Index 1 existiert nicht (nur 0)
    app.engine.remove_character(1)

    # Liste sollte unverändert sein
    assert len(app.engine.characters) == 1
    assert app.engine.characters[0] == c1
