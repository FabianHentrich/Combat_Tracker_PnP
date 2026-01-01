try:
    import pygame
except ImportError:
    pygame = None
import os
import time
from typing import List, Optional, Dict, Callable, Any
try:
    import mutagen
except ImportError:
    mutagen = None

class AudioController:
    def __init__(self):
        self.playlist: List[Dict[str, str]] = []  # List of {"title": str, "path": str, "type": "file"|"url", "duration": float}
        self.current_index: int = -1
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.5
        self.current_track_duration: float = 0.0
        self.last_request_time: float = 0.0
        self.min_request_interval: float = 1.0  # Minimum seconds between requests

        # Loop settings
        self.loop_single: bool = False
        self.loop_playlist: bool = False
        self.loop_count_target: int = 1  # Wie oft soll der Track gespielt werden (1 = einmal, kein Loop)
        self.current_loop_iteration: int = 0

        self.start_time_offset: float = 0.0
        self.saved_playback_position: float = 0.0

        self.on_track_end_callback: Optional[Callable] = None
        self.on_track_change_callback: Optional[Callable] = None

        self._initialized = False
        if pygame:
            try:
                pygame.mixer.init()
                if not pygame.get_init():
                    pygame.init()
                self._initialized = True
            except Exception as e:
                print(f"Error initializing pygame mixer: {e}")

            # Timer für Track-Ende Prüfung
            self._check_event_id = pygame.USEREVENT + 1
            if self._initialized:
                try:
                    pygame.mixer.music.set_endevent(self._check_event_id)
                except Exception as e:
                    print(f"Error setting endevent: {e}")
        else:
            print("Pygame not available. Audio features disabled.")

    def add_track(self, path: str, title: str = None):
        track_type = "file"
        # URL support removed as per user request

        if not title:
            title = os.path.basename(path)
        self.playlist.append({"title": title, "path": path, "type": track_type})

    def remove_track(self, index: int):
        if 0 <= index < len(self.playlist):
            self.playlist.pop(index)
            if index == self.current_index:
                self.stop()
                self.current_index = -1
            elif index < self.current_index:
                self.current_index -= 1


    def _get_duration(self, path: str) -> float:
        if not mutagen:
            return 0.0
        try:
            audio = mutagen.File(path)
            if audio and audio.info:
                return audio.info.length
        except Exception as e:
            print(f"Error getting duration for {path}: {e}")
        return 0.0

    def play(self, index: int = None, start_offset: float = 0.0):
        if not self._initialized:
            return

        if index is not None:
            self.current_index = index
            self.current_loop_iteration = 0
            # Wenn ein neuer Track explizit gewählt wird, ignorieren wir gespeicherte Positionen
            # es sei denn, start_offset wird explizit übergeben (was hier der Fall ist)
        else:
            # Resume logic if paused handled by caller or check here?
            # The UI calls pause() if playing. So play() is called when stopped or to restart.
            if self.saved_playback_position > 0:
                start_offset = self.saved_playback_position
                self.saved_playback_position = 0.0

        if 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            file_path = track["path"]


            # Get duration if not already known
            if "duration" not in track:
                track["duration"] = self._get_duration(file_path)
            self.current_track_duration = track["duration"]

            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(start=start_offset)
                self.start_time_offset = start_offset
                self.is_playing = True
                self.is_paused = False
                if self.on_track_change_callback:
                    self.on_track_change_callback(track)
            except Exception as e:
                print(f"Error playing track {file_path}: {e}")
                self.next_track()

    def pause(self):
        if not self._initialized:
            return
        if self.is_playing:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.pause()
                self.is_paused = True

    def stop(self):
        if not self._initialized:
            return
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def next_track(self):
        if not self.playlist:
            return

        next_index = self.current_index + 1
        if next_index >= len(self.playlist):
            if self.loop_playlist:
                next_index = 0
            else:
                self.stop()
                return

        self.play(next_index)

    def prev_track(self):
        if not self.playlist:
            return

        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist) - 1
        self.play(prev_index)

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self.volume)

    def move_track(self, from_index: int, to_index: int):
        if not (0 <= from_index < len(self.playlist)) or not (0 <= to_index <= len(self.playlist)): # to_index can be len if appending, but insert handles it.
            return

        # Clamp to_index to valid range for insert
        to_index = max(0, min(to_index, len(self.playlist) - 1))

        if from_index == to_index:
            return

        track = self.playlist.pop(from_index)
        self.playlist.insert(to_index, track)

        # Update current_index
        if self.current_index == from_index:
            self.current_index = to_index
        elif from_index < self.current_index and to_index >= self.current_index:
            self.current_index -= 1
        elif from_index > self.current_index and to_index <= self.current_index:
            self.current_index += 1

    def get_state(self) -> Dict[str, Any]:
        """Returns the current state of the audio controller for persistence."""
        return {
            "playlist": self.playlist,
            "current_index": self.current_index,
            "volume": self.volume,
            "loop_single": self.loop_single,
            "loop_playlist": self.loop_playlist,
            "loop_count_target": self.loop_count_target,
            "playback_position": self.get_playback_time()
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Restores the state of the audio controller."""
        if not state:
            return

        self.playlist = state.get("playlist", [])
        self.current_index = state.get("current_index", -1)
        self.volume = state.get("volume", 0.5)
        self.loop_single = state.get("loop_single", False)
        self.loop_playlist = state.get("loop_playlist", False)
        self.loop_count_target = state.get("loop_count_target", 1)
        self.saved_playback_position = state.get("playback_position", 0.0)

        self.set_volume(self.volume)

        # Restore duration if possible so UI shows correct total time
        if 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            # If it's a file, we can try to get duration. If URL, we might have it in track data
            if "duration" in track:
                self.current_track_duration = track["duration"]
            elif track["type"] == "file":
                self.current_track_duration = self._get_duration(track["path"])
                track["duration"] = self.current_track_duration

        # If we have a saved position, we consider it "paused" at that position
        if self.saved_playback_position > 0:
            self.is_paused = True
            # We don't set is_playing = True because pygame is not actually playing yet.
            # The UI should handle (is_paused and not is_playing) or check saved_playback_position.

        # Note: We don't auto-play on load to avoid sudden noise

    def check_events(self):
        """Should be called periodically from the main loop to check for music end events."""
        if not self._initialized:
            return

        try:
            for event in pygame.event.get():
                if event.type == self._check_event_id:
                    self._handle_track_end()
        except Exception as e:
            # Prevent crash if video system is not initialized or other pygame error
            pass

    def _handle_track_end(self):
        self.current_loop_iteration += 1

        if self.loop_single:
            # Infinite loop for single track
            self.play()
        elif self.current_loop_iteration < self.loop_count_target:
            # Repeat specific number of times
            self.play()
        else:
            # Move to next track
            self.next_track()

    def get_current_track_info(self) -> Optional[Dict]:
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def get_playback_time(self) -> float:
        if self._initialized and self.is_playing:
            pos = pygame.mixer.music.get_pos()
            if pos < 0:
                return 0.0
            return (pos / 1000.0) + self.start_time_offset

        if self.saved_playback_position > 0:
            return self.saved_playback_position

        return 0.0

    def get_total_duration(self) -> float:
        return self.current_track_duration
