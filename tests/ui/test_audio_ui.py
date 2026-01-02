import pytest
from unittest.mock import MagicMock, patch
import sys
from tests.mocks import MockScrollableFrame

# --- Fixtures ---

@pytest.fixture(scope="function")
def audio_ui_module(mock_tkinter, mock_pygame):
    # Force reload of the modules under test
    for mod in list(sys.modules.keys()):
        if mod.startswith('src'):
            del sys.modules[mod]

    import src.ui.components.audio.audio_player_view
    import src.ui.components.audio.audio_settings_view
    yield src.ui.components.audio.audio_player_view, src.ui.components.audio.audio_settings_view

@pytest.fixture
def root(mock_tkinter):
    return mock_tkinter.Tk()

@pytest.fixture
def controller():
    c = MagicMock()
    c.playlist = []
    c.current_index = -1
    c.is_playing = False
    c.is_paused = False
    c.loop_single = False
    c.loop_count_target = 1
    c.volume = 0.5
    c.get_current_track_info.return_value = None
    c.get_playback_time.return_value = 0
    c.get_total_duration.return_value = 0
    return c

# --- Tests ---

def test_player_widget_toggle_play(root, controller, audio_ui_module):
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget

    # Setup
    controller.playlist = [{"title": "Test", "path": "test.mp3"}]

    # AudioPlayerWidget does not use ScrollableFrame or ToolTip anymore
    widget = AudioPlayerWidget(root, controller, MagicMock())
    # Manually mock the button since setup_ui runs with mocked widgets
    widget.btn_play_pause = MagicMock()

    # Test Play (Initial)
    widget.toggle_play()
    controller.toggle_playback.assert_called()

    # Test Pause
    controller.is_playing = True
    widget.toggle_play()
    controller.toggle_playback.assert_called()

    # Test Unpause
    controller.is_paused = True
    widget.toggle_play()
    controller.toggle_playback.assert_called() # pause() toggles pause state

def test_player_widget_loop_controls(root, controller, audio_ui_module):
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget

    widget = AudioPlayerWidget(root, controller, MagicMock())

    # Use the MockVars created by setup_ui
    # widget.var_loop_active is a MockVar instance

    # Enable Loop (Infinite)
    widget.var_loop_active.set(True)
    widget.var_loop_count.set("Inf")
    widget.update_loop_state()


    assert controller.loop_single is True

    # Enable Loop (Count)
    widget.var_loop_count.set("5")
    widget.update_loop_state()

    assert controller.loop_single is False
    assert controller.loop_count_target == 5

    # Disable Loop
    widget.var_loop_active.set(False)
    widget.update_loop_state()

    assert controller.loop_single is False
    assert controller.loop_count_target == 1

def test_player_widget_mute(root, controller, audio_ui_module):
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget

    widget = AudioPlayerWidget(root, controller, MagicMock())

    # Initial state
    assert widget.is_muted is False

    # Mute
    widget.lbl_volume = MagicMock()

    # Simulate controller behavior
    def mock_toggle_mute():
        controller.volume = 0.0
    controller.toggle_mute.side_effect = mock_toggle_mute

    widget.toggle_mute()
    # Force UI update since we are mocking the loop or just call it manually
    widget.update_ui_loop()

    assert widget.is_muted is True
    assert widget.vol_var.get() == 0
    controller.toggle_mute.assert_called()
    widget.lbl_volume.config.assert_called_with(text="0%")

    # Unmute
    def mock_unmute():
        controller.volume = 0.5
    controller.toggle_mute.side_effect = mock_unmute

    widget.toggle_mute()
    widget.update_ui_loop()

    assert widget.is_muted is False
    assert widget.vol_var.get() > 0
    # We expect it to be called with something > 0%
    assert widget.lbl_volume.config.call_count == 2

def test_player_widget_volume_control(root, controller, audio_ui_module):
    AudioPlayerWidget = audio_ui_module[0].AudioPlayerWidget

    widget = AudioPlayerWidget(root, controller, MagicMock())
    widget.lbl_volume = MagicMock()

    # Test Volume Update
    widget.update_volume(50)
    controller.set_volume.assert_called_with(0.5)
    widget.lbl_volume.config.assert_called_with(text="50%")

    widget.update_volume(100)
    controller.set_volume.assert_called_with(1.0)
    widget.lbl_volume.config.assert_called_with(text="100%")

    widget.update_volume(0)
    controller.set_volume.assert_called_with(0.0)
    widget.lbl_volume.config.assert_called_with(text="0%")

def test_settings_window_add_file(root, controller, audio_ui_module):
    AudioSettingsWindow = audio_ui_module[1].AudioSettingsWindow

    with patch('src.ui.components.audio.audio_settings_view.filedialog') as mock_filedialog, \
         patch('src.ui.components.audio.audio_settings_view.ScrollableFrame', MockScrollableFrame), \
         patch('src.ui.components.audio.audio_settings_view.ToolTip', MagicMock()):

        mock_filedialog.askopenfilenames.return_value = ["test.mp3"]

        window = AudioSettingsWindow(root, controller)
        window.add_file()

        controller.add_track.assert_called_with("test.mp3")

def test_settings_window_add_folder(root, controller, audio_ui_module):
    AudioSettingsWindow = audio_ui_module[1].AudioSettingsWindow

    with patch('src.ui.components.audio.audio_settings_view.filedialog') as mock_filedialog, \
         patch('os.walk') as mock_walk, \
         patch('src.ui.components.audio.audio_settings_view.ScrollableFrame', MockScrollableFrame), \
         patch('src.ui.components.audio.audio_settings_view.ToolTip', MagicMock()):

        mock_filedialog.askdirectory.return_value = "/music"
        mock_walk.return_value = [("/music", [], ["test.mp3"])]

        window = AudioSettingsWindow(root, controller)
        window.add_folder()

        controller.add_track.assert_called()


def test_track_card_actions(root, controller, audio_ui_module):
    TrackCard = audio_ui_module[1].TrackCard
    track = {"title": "Test", "path": "test.mp3"}
    refresh_mock = MagicMock()

    with patch('src.ui.components.audio.audio_settings_view.ToolTip', MagicMock()):
        card = TrackCard(root, track, 0, controller, refresh_mock, MagicMock(), MagicMock(), MagicMock())

        # Test Play
        card.play_track()
        controller.play.assert_called_with(0)

        # Test Remove
        card.remove_track()
        controller.remove_track.assert_called_with(0)
        refresh_mock.assert_called()
