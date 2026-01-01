import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import importlib

@pytest.fixture
def audio_controller_and_mock(mock_pygame):
    # Reload audio_controller to ensure it uses the mocked pygame
    if 'src.controllers.audio_controller' in sys.modules:
        importlib.reload(sys.modules['src.controllers.audio_controller'])
    else:
        import src.controllers.audio_controller

    from src.controllers.audio_controller import AudioController

    # Setup mock for mixer.music.get_pos
    mock_pygame.mixer.music.get_pos.return_value = 10000 # 10 seconds

    controller = AudioController()
    # Manually set initialized because mock might interfere with __init__ logic check
    controller._initialized = True
    yield controller, mock_pygame

def test_add_track_file(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    path = "C:/Music/test.mp3"
    audio_controller.add_track(path)

    assert len(audio_controller.playlist) == 1
    assert audio_controller.playlist[0]["path"] == path
    assert audio_controller.playlist[0]["title"] == "test.mp3"
    assert audio_controller.playlist[0]["type"] == "file"


def test_play_track(audio_controller_and_mock):
    audio_controller, mock_pygame = audio_controller_and_mock
    audio_controller.add_track("test.mp3")
    audio_controller.play(0)

    assert audio_controller.current_index == 0
    assert audio_controller.is_playing is True
    assert audio_controller.is_paused is False

    # Verify pygame calls
    mock_pygame.mixer.music.load.assert_called_with("test.mp3")
    mock_pygame.mixer.music.play.assert_called()

def test_pause_unpause(audio_controller_and_mock):
    audio_controller, mock_pygame = audio_controller_and_mock
    audio_controller.add_track("test.mp3")
    audio_controller.play(0)

    # Pause
    audio_controller.pause()
    assert audio_controller.is_paused is True
    mock_pygame.mixer.music.pause.assert_called()

    # Unpause
    audio_controller.pause()
    assert audio_controller.is_paused is False
    mock_pygame.mixer.music.unpause.assert_called()

def test_next_track(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")

    audio_controller.play(0)
    audio_controller.next_track()

    assert audio_controller.current_index == 1
    assert audio_controller.playlist[1]["title"] == "track2.mp3"

def test_prev_track(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")

    audio_controller.play(1)
    audio_controller.prev_track()

    assert audio_controller.current_index == 0
    assert audio_controller.playlist[0]["title"] == "track1.mp3"

def test_loop_single_track(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")

    audio_controller.play(0)
    audio_controller.loop_single = True

    # Simulate track end
    audio_controller._handle_track_end()

    # Should still be on track 0
    assert audio_controller.current_index == 0
    assert audio_controller.current_loop_iteration == 1

def test_loop_playlist(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")

    audio_controller.play(1)
    audio_controller.loop_playlist = True

    # Simulate track end (next track)
    audio_controller._handle_track_end()

    # Should loop back to 0
    assert audio_controller.current_index == 0

def test_remove_track(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")
    audio_controller.add_track("track3.mp3")

    audio_controller.play(1) # Playing track2

    # Remove track1 (before current)
    audio_controller.remove_track(0)
    assert len(audio_controller.playlist) == 2
    assert audio_controller.current_index == 0 # Should shift down
    assert audio_controller.playlist[0]["title"] == "track2.mp3"

    # Remove track3 (after current)
    audio_controller.remove_track(1)
    assert len(audio_controller.playlist) == 1
    assert audio_controller.current_index == 0

    # Remove current track
    audio_controller.remove_track(0)
    assert len(audio_controller.playlist) == 0
    assert audio_controller.current_index == -1
    assert audio_controller.is_playing is False


def test_stop(audio_controller_and_mock):
    audio_controller, mock_pygame = audio_controller_and_mock
    audio_controller.add_track("test.mp3")
    audio_controller.play(0)

    audio_controller.stop()

    assert audio_controller.is_playing is False
    assert audio_controller.is_paused is False
    mock_pygame.mixer.music.stop.assert_called()

def test_set_volume(audio_controller_and_mock):
    audio_controller, mock_pygame = audio_controller_and_mock
    audio_controller.set_volume(0.8)
    assert audio_controller.volume == 0.8
    mock_pygame.mixer.music.set_volume.assert_called_with(0.8)

    # Test clamping
    audio_controller.set_volume(1.5)
    assert audio_controller.volume == 1.0

    audio_controller.set_volume(-0.5)
    assert audio_controller.volume == 0.0

def test_audio_state_persistence(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock

    # Setup state
    audio_controller.add_track("track1.mp3")
    audio_controller.current_index = 0
    audio_controller.volume = 0.7
    audio_controller.loop_single = True
    audio_controller.loop_playlist = False
    audio_controller.loop_count_target = 5

    # Get state
    state = audio_controller.get_state()

    assert state["current_index"] == 0
    assert state["volume"] == 0.7
    assert state["loop_single"] is True
    assert len(state["playlist"]) == 1

    # Create new controller and load state
    new_controller = audio_controller.__class__()
    # Mock pygame for new controller if needed, but __init__ handles import error gracefully or we can patch
    with patch('src.controllers.audio_controller.pygame', MagicMock()):
        new_controller.load_state(state)

        assert new_controller.current_index == 0
        assert new_controller.volume == 0.7
        assert new_controller.loop_single is True
        assert len(new_controller.playlist) == 1
        assert new_controller.playlist[0]["path"] == "track1.mp3"

def test_state_persistence_with_position(audio_controller_and_mock):
    audio_controller, mock_pygame = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.play(0)

    # Simulate playback time
    mock_pygame.mixer.music.get_pos.return_value = 5000 # 5 seconds
    audio_controller.start_time_offset = 10.0 # Started at 10s

    state = audio_controller.get_state()

    assert state["playback_position"] == 15.0
    assert state["current_index"] == 0

    # Create new controller and load state
    # We need to ensure the class is imported correctly
    from src.controllers.audio_controller import AudioController
    new_controller = AudioController()
    new_controller.load_state(state)

    assert new_controller.saved_playback_position == 15.0
    assert new_controller.current_index == 0

    # Test resume from saved position
    new_controller._initialized = True

    # Reset mock to check new calls
    mock_pygame.mixer.music.play.reset_mock()

    # We need to patch pygame inside the module where AudioController is defined
    # But since we are using the same mock object that was injected into the module via fixture (hopefully)
    # Let's check if play() uses the mocked pygame.
    # The fixture 'audio_controller_and_mock' reloads the module, so 'src.controllers.audio_controller.pygame' should be 'mock_pygame'.

    # However, 'new_controller' is a fresh instance.
    # We need to make sure it sees the mock.
    # Since we reloaded the module in the fixture, the class definition uses the mock.
    # So new_controller should use the mock.

    # Add track to new controller so it can play
    new_controller.add_track("track1.mp3")

    new_controller.play() # Resume
    mock_pygame.mixer.music.play.assert_called_with(start=15.0)

def test_move_track(audio_controller_and_mock):
    audio_controller, _ = audio_controller_and_mock
    audio_controller.add_track("track1.mp3")
    audio_controller.add_track("track2.mp3")
    audio_controller.add_track("track3.mp3")

    # Move track 0 to 1
    # [1, 2, 3] -> [2, 1, 3]
    audio_controller.move_track(0, 1)
    assert audio_controller.playlist[0]["title"] == "track2.mp3"
    assert audio_controller.playlist[1]["title"] == "track1.mp3"
    assert audio_controller.playlist[2]["title"] == "track3.mp3"

    # Move track 2 to 0
    # [2, 1, 3] -> [3, 2, 1]
    audio_controller.move_track(2, 0)
    assert audio_controller.playlist[0]["title"] == "track3.mp3"
    assert audio_controller.playlist[1]["title"] == "track2.mp3"
    assert audio_controller.playlist[2]["title"] == "track1.mp3"

    # Test current_index update
    audio_controller.play(1) # Playing track2 (index 1)
    assert audio_controller.current_index == 1

    # Move track 1 (playing) to 2
    # [3, 2, 1] -> [3, 1, 2]
    audio_controller.move_track(1, 2)
    assert audio_controller.playlist[2]["title"] == "track2.mp3"
    assert audio_controller.current_index == 2 # Should update to new index

