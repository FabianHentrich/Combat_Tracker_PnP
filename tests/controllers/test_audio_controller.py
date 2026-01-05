import pytest
from unittest.mock import MagicMock, patch
import sys

# This setup ensures that 'pygame' and 'mutagen' are mocked *before* the controller is imported.
MOCK_PYGAME = MagicMock()
MOCK_MUTAGEN = MagicMock()

# Ensure that any iteration over pygame.event.get() is finite and does not block.
MOCK_PYGAME.event.get.return_value = []

@pytest.fixture
def audio_controller():
    """Provides a clean AudioController instance with mocked dependencies."""
    # Patch the modules directly in the namespace of the module under test.
    # This is more robust than patching sys.modules.
    with patch('src.controllers.audio_controller.pygame', MOCK_PYGAME), \
         patch('src.controllers.audio_controller.mutagen', MOCK_MUTAGEN):
        
        # Reset mocks for every test function to ensure isolation
        MOCK_PYGAME.reset_mock()
        MOCK_MUTAGEN.reset_mock()
        
        # Configure mock for _get_duration to return a float, preventing potential errors
        MOCK_MUTAGEN.File.return_value.info.length = 180.0  # e.g., 3 minutes

        # Import the controller *after* the patches are applied
        from src.controllers.audio_controller import AudioController
        controller = AudioController()
        controller._initialized = True
        yield controller

# --- Tests ---

def test_add_and_remove_track(audio_controller):
    """Tests adding and removing tracks and index management."""
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")
    assert len(audio_controller.playlist) == 2

    audio_controller.current_index = 1
    audio_controller.remove_track(0) # Remove track before the current one
    assert len(audio_controller.playlist) == 1
    assert audio_controller.current_index == 0 # Index should be updated

def test_play_track_loads_file(audio_controller):
    """Tests that play() calls the necessary pygame methods."""
    audio_controller.add_track("test.mp3")
    audio_controller.play(0)
    
    MOCK_PYGAME.mixer.music.load.assert_called_with("test.mp3")
    MOCK_PYGAME.mixer.music.play.assert_called()

def test_next_track_with_loop(audio_controller):
    """
    Tests that next_track correctly loops to the beginning of the playlist.
    This test now patches the 'play' method to avoid any potential UI/event loops.
    """
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")
    audio_controller.loop_playlist = True
    audio_controller.current_index = 1 # At the end of the playlist

    with patch.object(audio_controller, 'play') as mock_play:
        audio_controller.next_track()
        # We expect it to call play with the index of the first track
        mock_play.assert_called_once_with(0)

def test_next_track_no_loop(audio_controller):
    """Tests that playback stops at the end of the playlist if loop is off."""
    audio_controller.add_track("track1.mp3")
    audio_controller.current_index = 0
    audio_controller.loop_playlist = False

    with patch.object(audio_controller, 'play') as mock_play:
        audio_controller.next_track()
        # It should call the mixer's stop function and NOT call play again
        MOCK_PYGAME.mixer.music.stop.assert_called_once()
        mock_play.assert_not_called()
