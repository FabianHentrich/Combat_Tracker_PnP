import pytest
from unittest.mock import MagicMock, patch
import sys

# We patch the module-level pygame variable in src.controllers.audio_controller
# This works even if the module is already imported.

@pytest.fixture
def audio_controller():
    with patch('src.controllers.audio_controller.pygame') as mock_pygame, \
         patch('src.controllers.audio_controller.mutagen') as mock_mutagen:

        # Setup mock pygame
        mock_pygame.mixer.music.get_busy.return_value = False
        # Ensure pygame.error is an Exception class
        mock_pygame.error = Exception

        from src.controllers.audio_controller import AudioController
        controller = AudioController()
        # Force initialization state for tests
        controller._initialized = True

        # Attach mock to controller for easy access in tests if needed,
        # though we usually access it via the patch context in the test.
        # But since we are inside a fixture, we can't yield the mock easily with the controller.
        # We will re-patch in tests or assume the fixture set it up correctly.

        return controller

def test_initialization(audio_controller):
    """Testet die Initialisierung des AudioControllers."""
    assert audio_controller._initialized is True
    assert audio_controller.volume == 0.5

def test_add_track(audio_controller):
    """Testet das Hinzufügen von Tracks zur Playlist."""
    path = "test.mp3"
    title = "Test Track"
    audio_controller.add_track(path, title)
    assert len(audio_controller.playlist) == 1
    assert audio_controller.playlist[0]["title"] == title
    assert audio_controller.playlist[0]["path"] == path

def test_play_track(audio_controller):
    """Testet das Abspielen eines Tracks."""
    path = "test.mp3"
    title = "Test Track"
    audio_controller.add_track(path, title)

    # We need to patch again to get access to the mock object for assertions
    with patch('src.controllers.audio_controller.pygame') as mock_pygame:
        # Ensure pygame appears initialized
        mock_pygame.get_init.return_value = True

        audio_controller.play(0)

        mock_pygame.mixer.music.load.assert_called_with("test.mp3")
        mock_pygame.mixer.music.play.assert_called()
        assert audio_controller.is_playing is True
        assert audio_controller.current_index == 0

def test_volume_control(audio_controller):
    """Testet die Lautstärkeregelung."""
    with patch('src.controllers.audio_controller.pygame') as mock_pygame:
        mock_pygame.get_init.return_value = True

        audio_controller.set_volume(0.8)
        assert audio_controller.volume == 0.8
        mock_pygame.mixer.music.set_volume.assert_called_with(0.8)

def test_toggle_mute(audio_controller):
    """Testet Mute/Unmute."""
    with patch('src.controllers.audio_controller.pygame') as mock_pygame:
        mock_pygame.get_init.return_value = True

        audio_controller.set_volume(0.5)
        # Reset mock calls to verify subsequent calls
        mock_pygame.mixer.music.set_volume.reset_mock()

        # Mute
        audio_controller.toggle_mute()
        assert audio_controller.volume == 0.0
        mock_pygame.mixer.music.set_volume.assert_called_with(0.0)

        # Unmute
        audio_controller.toggle_mute()
        assert audio_controller.volume == 0.5
        mock_pygame.mixer.music.set_volume.assert_called_with(0.5)

