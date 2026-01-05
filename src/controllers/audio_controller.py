try:
    import pygame
except ImportError:
    pygame = None
import os
from typing import List, Optional, Dict, Callable, Any
try:
    import mutagen
except ImportError:
    mutagen = None

from src.utils.logger import setup_logging

logger = setup_logging()


def _get_duration(path: str) -> float:
    if not mutagen: return 0.0
    try:
        audio = mutagen.File(path)
        if audio and audio.info:
            return audio.info.length
    except Exception as e:
        logger.error(f"Error getting duration for {path}: {e}")
    return 0.0


class AudioController:
    """
    Manages audio playback, including playlist, volume, and looping.
    """
    def __init__(self):
        self.playlist: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.5
        self.current_track_duration: float = 0.0
        self.loop_single: bool = False
        self.loop_playlist: bool = False
        self.loop_count_target: int = 1
        self.current_loop_iteration: int = 0
        self.start_time_offset: float = 0.0
        self.saved_playback_position: float = 0.0
        self.on_track_end_callback: Optional[Callable] = None
        self._track_change_listeners: List[Callable] = []
        self.last_vol: float = 0.5
        self._initialized = False
        self.init_error = None
        self._check_event_id = None

        self._initialize_audio_system()

    def _initialize_audio_system(self):
        if pygame:
            try:
                # Initialize only the mixer to avoid creating a window
                pygame.mixer.init()
                self._initialized = True
                self._check_event_id = pygame.USEREVENT + 1
                pygame.mixer.music.set_endevent(self._check_event_id)
            except Exception as e:
                self.init_error = str(e)
                logger.error(f"Error initializing pygame mixer: {e}")
        else:
            self.init_error = "Pygame module not found."
            logger.warning("Pygame not available. Audio features disabled.")

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def add_track(self, path: str, title: str = None):
        if not title:
            title = os.path.basename(path)
        self.playlist.append({"title": title, "path": path, "type": "file"})

    def remove_track(self, index: int):
        if 0 <= index < len(self.playlist):
            self.playlist.pop(index)
            if index == self.current_index:
                self.stop()
                self.current_index = -1
            elif index < self.current_index:
                self.current_index -= 1

    def play(self, index: int = None, start_offset: float = 0.0):
        if not self._initialized: return
        if index is not None:
            self.current_index = index
            self.current_loop_iteration = 0
        else:
            if self.saved_playback_position > 0:
                start_offset = self.saved_playback_position
                self.saved_playback_position = 0.0

        if 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            file_path = track["path"]
            if "duration" not in track:
                track["duration"] = _get_duration(file_path)
            self.current_track_duration = track["duration"]

            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(start=start_offset)
                self.start_time_offset = start_offset
                self.is_playing = True
                self.is_paused = False
                for listener in self._track_change_listeners:
                    listener(track)
            except Exception as e:
                logger.error(f"Error playing track {file_path}: {e}")
                self.next_track()

    def pause(self):
        if not self._initialized: return
        if self.is_playing:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.pause()
                self.is_paused = True

    def stop(self):
        if not self._initialized: return
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def next_track(self):
        if not self.playlist: return
        next_index = self.current_index + 1
        if next_index >= len(self.playlist):
            if self.loop_playlist:
                next_index = 0
            else:
                self.stop()
                return
        self.play(next_index)

    def prev_track(self):
        if not self.playlist: return
        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist) - 1
        self.play(prev_index)

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self.volume)

    def move_track(self, from_index: int, to_index: int):
        if not (0 <= from_index < len(self.playlist) and 0 <= to_index < len(self.playlist)): return
        if from_index == to_index: return
        track = self.playlist.pop(from_index)
        self.playlist.insert(to_index, track)
        if self.current_index == from_index:
            self.current_index = to_index
        elif from_index < self.current_index <= to_index:
            self.current_index -= 1
        elif from_index > self.current_index >= to_index:
            self.current_index += 1

    def get_state(self) -> Dict[str, Any]:
        return {
            "playlist": self.playlist, "current_index": self.current_index, "volume": self.volume,
            "loop_single": self.loop_single, "loop_playlist": self.loop_playlist,
            "loop_count_target": self.loop_count_target, "playback_position": self.get_playback_time()
        }

    def load_state(self, state: Dict[str, Any]):
        if not state: return
        self.playlist = state.get("playlist", [])
        self.current_index = state.get("current_index", -1)
        self.volume = state.get("volume", 0.5)
        self.loop_single = state.get("loop_single", False)
        self.loop_playlist = state.get("loop_playlist", False)
        self.loop_count_target = state.get("loop_count_target", 1)
        self.saved_playback_position = state.get("playback_position", 0.0)
        self.set_volume(self.volume)
        if 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            if "duration" in track:
                self.current_track_duration = track["duration"]
            elif track.get("type") == "file":
                self.current_track_duration = _get_duration(track["path"])
                track["duration"] = self.current_track_duration

    def check_events(self):
        if not self._initialized: return
        try:
            for event in pygame.event.get():
                if event.type == self._check_event_id:
                    self._handle_track_end()
        except Exception:
            pass

    def _handle_track_end(self):
        self.current_loop_iteration += 1
        if self.loop_single:
            self.play()
        elif self.current_loop_iteration < self.loop_count_target:
            self.play()
        else:
            self.next_track()

    def get_current_track_info(self) -> Optional[Dict]:
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def get_playback_time(self) -> float:
        if self._initialized and self.is_playing:
            pos = pygame.mixer.music.get_pos()
            return (pos / 1000.0) + self.start_time_offset if pos >= 0 else 0.0
        return self.saved_playback_position if self.saved_playback_position > 0 else 0.0

    def get_total_duration(self) -> float:
        return self.current_track_duration

    def toggle_playback(self):
        if self.is_playing and not self.is_paused: self.pause()
        elif self.is_paused: self.pause()
        else:
            if self.current_index == -1 and self.playlist: self.play(0)
            else: self.play()

    def increase_volume(self, step: float = 0.05):
        self.set_volume(min(1.0, self.volume + step))

    def decrease_volume(self, step: float = 0.05):
        self.set_volume(max(0.0, self.volume - step))

    def toggle_mute(self):
        if self.volume > 0:
            self.last_vol = self.volume
            self.set_volume(0)
        else:
            self.set_volume(getattr(self, 'last_vol', 0.5) or 0.5)

    def add_track_change_listener(self, listener: Callable):
        if listener not in self._track_change_listeners:
            self._track_change_listeners.append(listener)

    def remove_track_change_listener(self, listener: Callable):
        if listener in self._track_change_listeners:
            self._track_change_listeners.remove(listener)
