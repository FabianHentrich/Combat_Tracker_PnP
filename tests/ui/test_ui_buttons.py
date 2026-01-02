import pytest
from unittest.mock import MagicMock, patch
import sys
import importlib
from src.models.character import Character
from src.models.enums import CharacterType

@pytest.fixture
def app(mock_tkinter):
    # Reload main_view to ensure it binds to the mocked tkinter
    if 'src.ui.main_view' in sys.modules:
        importlib.reload(sys.modules['src.ui.main_view'])
    else:
        import src.ui.main_view

    # Reload main_window to ensure it imports the reloaded MainView
    if 'src.ui.main_window' in sys.modules:
        importlib.reload(sys.modules['src.ui.main_window'])
    else:
        import src.ui.main_window

    # Reload combat_action_handler if present
    if 'src.controllers.combat_action_handler' in sys.modules:
        importlib.reload(sys.modules['src.controllers.combat_action_handler'])

    from src.ui.main_window import CombatTracker

    # Patch MainView in main_window to return a MagicMock instance
    # This prevents setup_ui from running real code if we don't want it to,
    # but since we mocked tkinter, running setup_ui is also fine (and maybe better to test integration).
    # However, to strictly test buttons -> controller -> engine, mocking view is safer.

    with patch('src.ui.main_window.MainView') as MockMainView:
        root = MagicMock()
        tracker = CombatTracker(root)

        # tracker.view is the mock instance
        tracker.view = MockMainView.return_value

        tracker.engine.characters = []
        tracker.engine.turn_index = -1
        tracker.engine.round_number = 1

        yield tracker

def test_btn_add_character(app):
    """Testet den 'Hinzufügen' Button (Quick Add)."""
    # Setup View Input
    app.view.get_quick_add_data.return_value = {
        "name": "TestChar",
        "lp": 20,
        "rp": 5,
        "sp": 0,
        "init": 10,
        "gew": 2,
        "type": CharacterType.PLAYER,
        "surprise": False
    }

    # Action
    app.character_handler.add_character_quick()

    # Assert
    assert len(app.engine.characters) == 1
    char = app.engine.characters[0]
    assert char.name == "TestChar"
    assert char.lp == 20
    assert char.char_type == CharacterType.PLAYER

    # Verify view updates
    app.view.update_listbox.assert_called()
    app.view.clear_quick_add_fields.assert_called()

def test_btn_roll_initiative(app):
    """Testet den 'Initiative würfeln' Button."""
    c1 = Character("A", 10, 10, 10, 0, gew=5)
    c2 = Character("B", 10, 10, 10, 0, gew=5)
    app.engine.characters = [c1, c2]

    # Action
    app.combat_handler.roll_initiative_all()

    # Assert
    assert app.engine.initiative_rolled is True
    assert app.engine.turn_index == 0 # First char active
    assert c1.init > 0
    assert c2.init > 0
    app.view.log_message.assert_called()

def test_btn_next_turn(app):
    """Testet den 'Nächster Zug' Button."""
    c1 = Character("A", 10, 10, 10, 20)
    c2 = Character("B", 10, 10, 10, 10)
    app.engine.characters = [c1, c2]
    app.engine.initiative_rolled = True
    app.engine.turn_index = 0

    # Action
    app.combat_handler.next_turn()

    # Assert
    assert app.engine.turn_index == 1
    assert app.engine.characters[1] == c2

def test_btn_deal_damage(app):
    """Testet den 'Schaden' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    # Mock Selection
    app.view.get_selected_char_id.return_value = "uuid-1"
    # Mock Input
    app.view.get_action_value.return_value = 5
    app.view.get_action_type.return_value = "Normal"
    app.view.get_status_input.return_value = {"rank": 1}

    # Action
    app.combat_handler.deal_damage()

    # Assert
    assert c1.lp == 15
    app.view.log_message.assert_called()

def test_btn_heal(app):
    """Testet den 'Heilen' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.lp = 10
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    app.view.get_selected_char_id.return_value = "uuid-1"
    app.view.get_action_value.return_value = 5

    # Action
    app.combat_handler.apply_healing()

    # Assert
    assert c1.lp == 15

def test_btn_shield(app):
    """Testet den 'Schild +' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    app.view.get_selected_char_id.return_value = "uuid-1"
    app.view.get_action_value.return_value = 3

    # Action
    app.combat_handler.apply_shield()

    # Assert
    assert c1.sp == 3

def test_btn_armor(app):
    """Testet den 'Rüstung +' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    app.view.get_selected_char_id.return_value = "uuid-1"
    app.view.get_action_value.return_value = 2

    # Action
    app.combat_handler.apply_armor()

    # Assert
    assert c1.rp == 2

def test_btn_add_status(app):
    """Testet den 'Status hinzufügen' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    app.view.get_selected_char_id.return_value = "uuid-1"
    app.view.get_status_input.return_value = {
        "status": "Vergiftung",
        "duration": "3",
        "rank": "1"
    }

    # Action
    app.combat_handler.add_status_to_character()

    # Assert
    assert len(c1.status) == 1
    assert c1.status[0].name == "Vergiftung"
    assert c1.status[0].duration == 3

def test_btn_delete_character(app):
    """Testet den 'Löschen' Button."""
    c1 = Character("Target", 20, 0, 0, 10)
    c1.id = "uuid-1"
    app.engine.characters = [c1]

    app.view.get_selected_char_id.return_value = "uuid-1"

    # Action
    app.character_handler.delete_character()

    # Assert
    assert len(app.engine.characters) == 0

def test_btn_reset_initiative(app):
    """Testet den 'Init Reset' Button."""
    c1 = Character("A", 10, 10, 10, 20)
    app.engine.characters = [c1]
    app.engine.initiative_rolled = True

    # Action
    app.combat_handler.reset_initiative("All")

    # Assert
    assert c1.init == 0
    assert app.engine.initiative_rolled is False

def test_btn_undo_redo(app):
    """Testet Undo und Redo Buttons."""
    # Initialize with 0 SP and 0 RP to ensure damage hits LP
    c1 = Character("A", 10, 0, 0, 10)
    app.engine.characters = [c1]

    # Change state (Damage)
    c1.id = "uuid-1"
    app.view.get_selected_char_id.return_value = "uuid-1"
    app.view.get_action_value.return_value = 5
    app.view.get_action_type.return_value = "Normal"
    app.view.get_status_input.return_value = {"rank": 1}

    app.combat_handler.deal_damage()
    assert c1.lp == 5

    # Undo
    app.history_manager.undo()
    # Note: Undo restores state, which replaces character objects.
    # We need to fetch the character again from engine
    c1_restored = app.engine.characters[0]
    assert c1_restored.lp == 10

    # Redo
    app.history_manager.redo()
    c1_redo = app.engine.characters[0]
    assert c1_redo.lp == 5

def test_btn_open_audio_settings(app):
    """Testet den Button zum Öffnen der Audio-Einstellungen."""
    # Mock AudioSettingsWindow
    with patch('src.ui.components.audio.audio_settings_view.AudioSettingsWindow') as MockAudioSettings:
        app.open_audio_settings()
        MockAudioSettings.assert_called_once()
