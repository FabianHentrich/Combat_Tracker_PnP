import pytest
from unittest.mock import MagicMock, patch, ANY
import sys
from tests.mocks import MockScrollableFrame

# --- Fixtures ---

@pytest.fixture(scope="module")
def audio_ui_module():
    """Importiert die Audio-UI-Module ohne Patchen der Basisklassen."""
    import src.ui.components.audio.audio_player_view as player_view
    import src.ui.components.audio.audio_settings_view as settings_view
    import src.ui.components.audio.track_card as track_card_module
    yield player_view, settings_view, track_card_module

@pytest.fixture
def root():
    """Provides a mocked Tk root."""
    return MagicMock()

@pytest.fixture
def controller():
    """Provides a mocked AudioController with corrected event handling for tests."""
    c = MagicMock()
    c.playlist = []
    c.current_index = -1
    c.is_playing = False
    c.is_paused = False
    c.loop_single = False
    c.loop_playlist = False
    c.loop_count_target = 1
    c.volume = 0.5
    c.get_current_track_info.return_value = None
    c.get_playback_time.return_value = 0
    c.get_total_duration.return_value = 0
    
    # FIX: Prevent infinite loops by making pygame.event.get() return an empty list.
    # This is necessary because the AudioController's check_events() iterates over it.
    # We mock this on the controller's internal pygame reference if it exists.
    if hasattr(c, 'pygame'):
        c.pygame.event.get.return_value = []
        
    return c

# --- AudioPlayerWidget Tests ---

def test_player_widget_ui_update(root, controller, audio_ui_module):
    """Tests that the UI loop correctly updates labels und buttons."""
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget
    with patch('tkinter.StringVar'):
        with patch.object(AudioPlayerWidget, 'setup_ui'), \
             patch.object(AudioPlayerWidget, 'update_ui_loop'):
            widget = AudioPlayerWidget(root, controller, MagicMock())
        with patch.object(widget, 'after') as mock_after:
            widget.lbl_title = MagicMock()
            widget.lbl_time = MagicMock()
            widget.btn_play_pause = MagicMock()

            controller.is_playing = True
            controller.get_current_track_info.return_value = {"title": "Test Song"}
            controller.current_index = 0
            controller.get_playback_time.return_value = 30
            controller.get_total_duration.return_value = 180

            from src.ui.components.audio.audio_player_view import AudioPlayerWidget as APW
            APW.update_ui_loop(widget)
            mock_after.assert_called()

    widget.lbl_title.config.assert_called_with(text="1. Test Song")
    widget.lbl_time.config.assert_called_with(text="00:30 / 03:00")


def test_player_widget_loop_state(root, controller, audio_ui_module):
    """Tests the logic of the loop controls."""
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget
    with patch('tkinter.StringVar'):
        with patch.object(AudioPlayerWidget, 'setup_ui'), \
             patch.object(AudioPlayerWidget, 'update_ui_loop'):
            widget = AudioPlayerWidget(root, controller, MagicMock())
    widget.var_loop_active = MagicMock()
    widget.var_loop_count = MagicMock()
    widget.var_loop_all = MagicMock()

    widget.var_loop_active.get.return_value = True
    widget.var_loop_count.get.return_value = "Inf"
    widget.update_loop_state()
    assert controller.loop_single is True

# --- AudioSettingsWindow Tests ---

@patch('src.ui.components.audio.audio_settings_view.filedialog.askopenfilenames')
def test_settings_window_add_file(mock_dialog, root, controller, audio_ui_module):
    """Tests that adding a file calls the controller and refreshes the playlist."""
    AudioSettingsWindow = audio_ui_module[1].AudioSettingsWindow
    mock_dialog.return_value = ["/path/to/song.mp3"]
    
    with patch.object(AudioSettingsWindow, 'refresh_playlist') as mock_refresh:
        window = AudioSettingsWindow(root, controller, {})
        window.add_file()
        
        controller.add_track.assert_called_once_with("/path/to/song.mp3")
        mock_refresh.assert_called_once()

# --- TrackCard Tests ---

def test_track_card_remove_track(root, controller, audio_ui_module):
    """Tests that the remove button on a track card calls the correct methods."""
    TrackCard = audio_ui_module[2].TrackCard
    refresh_mock = MagicMock()
    
    card = TrackCard(root, {}, 0, controller, refresh_mock, MagicMock(), MagicMock(), MagicMock())
    
    card.remove_track()
    
    controller.remove_track.assert_called_with(0)
    refresh_mock.assert_called_once()
