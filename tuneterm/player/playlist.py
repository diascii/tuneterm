import logging
import random
import threading
import urllib.request
from enum import Enum
from typing import List, Optional
from tuneterm.player.metadata import TrackInfo, extract_metadata
from tuneterm.player.streaming import get_youtube_stream_info

_log = logging.getLogger("tuneterm")

class RepeatMode(Enum):
    OFF = 0
    ALL = 1
    ONE = 2

class Playlist:
    def __init__(self):
        self._lock = threading.RLock()
        self._tracks: List[TrackInfo] = []
        self._shuffled_indices: List[int] = []
        self._current_index: int = -1
        self._is_shuffled: bool = False
        self._repeat_mode: RepeatMode = RepeatMode.OFF
        # Track history for back navigation when shuffled
        self.history: List[int] = []

    @property
    def tracks(self) -> List[TrackInfo]:
        with self._lock:
            return list(self._tracks)

    @property
    def current_index(self) -> int:
        with self._lock:
            return self._current_index

    @current_index.setter
    def current_index(self, value: int):
        with self._lock:
            if not self._tracks:
                self._current_index = -1
            elif value == -1:
                self._current_index = -1
            elif 0 <= value < len(self._tracks):
                self._current_index = value
            else:
                # Clamp out-of-bound indices
                if value < 0 or value >= len(self._tracks):
                    self._current_index = -1
                else:
                    self._current_index = value

    @property
    def is_shuffled(self) -> bool:
        with self._lock:
            return self._is_shuffled

    @is_shuffled.setter
    def is_shuffled(self, value: bool):
        with self._lock:
            self._is_shuffled = value

    @property
    def repeat_mode(self) -> RepeatMode:
        with self._lock:
            return self._repeat_mode

    @repeat_mode.setter
    def repeat_mode(self, value: RepeatMode):
        with self._lock:
            self._repeat_mode = value

    def add(self, filepath: str) -> TrackInfo:
        if filepath.startswith("http://") or filepath.startswith("https://"):
            info_dict = get_youtube_stream_info(filepath)
            raw_url = info_dict.get("url")
            if not raw_url:
                raw_url = filepath
                
            title = info_dict.get("title", "Streaming Audio")
            artist = info_dict.get("artist", filepath)
            
            cover_bytes = None
            thumb_url = info_dict.get("thumbnail")
            if thumb_url:
                try:
                    req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        cover_bytes = resp.read()
                except Exception as e:
                    _log.debug("[Playlist] Gagal download thumbnail: %s", e)
                
            info = TrackInfo(
                filepath=raw_url,
                title=title,
                artist=artist,
                album="YouTube",
                year="",
                genre="Stream",
                duration=0.0,
                bitrate=0,
                sample_rate=0,
                format="Stream",
                cover_art_bytes=cover_bytes,
                thumb_url=thumb_url,
                original_url=filepath
            )
        else:
            info = extract_metadata(filepath)
            info.original_url = filepath
            
        with self._lock:
            self._tracks.append(info)
            if self._is_shuffled:
                # Insert at a random position in the remaining queue, or just append
                self._shuffled_indices.append(len(self._tracks) - 1)
            return info

    def add_lazy_spotify(self, title: str, artist: str, cover_url: Optional[str] = None) -> TrackInfo:
        with self._lock:
            info = TrackInfo(
                filepath="",
                title=title,
                artist=artist,
                album="Spotify",
                year="",
                genre="Spotify",
                duration=0.0,
                bitrate=0,
                sample_rate=0,
                format="youtube",
                thumb_url=cover_url,
                original_url=None,
                is_unresolved=True,
                search_query=f"ytsearch1:{artist} {title}"
            )
            self._tracks.append(info)
            if self._is_shuffled:
                self._shuffled_indices.append(len(self._tracks) - 1)
            return info

    def add_track_info(self, info: TrackInfo) -> TrackInfo:
        with self._lock:
            self._tracks.append(info)
            if self._is_shuffled:
                self._shuffled_indices.append(len(self._tracks) - 1)
            return info

    def remove(self, index: int):
        with self._lock:
            if 0 <= index < len(self._tracks):
                self._tracks.pop(index)
                if self._current_index == index:
                    self._current_index = -1
                elif self._current_index > index:
                    self._current_index -= 1
                
                # Update history thread-safely
                new_history = []
                for h in self.history:
                    if h == index:
                        continue
                    elif h > index:
                        new_history.append(h - 1)
                    else:
                        new_history.append(h)
                self.history = [h for h in new_history if 0 <= h < len(self._tracks)]
                
                self._rebuild_shuffle()

    def move_track(self, from_index: int, to_index: int) -> bool:
        """Move track from `from_index` to `to_index`. Returns True if moved."""
        with self._lock:
            if not (0 <= from_index < len(self._tracks) and 0 <= to_index < len(self._tracks)):
                return False
            if from_index == to_index:
                return False

            track = self._tracks.pop(from_index)
            self._tracks.insert(to_index, track)

            # Update current_index if affected
            if self._current_index == from_index:
                self._current_index = to_index
            elif from_index < self._current_index <= to_index:
                self._current_index -= 1
            elif to_index <= self._current_index < from_index:
                self._current_index += 1

            # Update history indices
            new_history = []
            for h in self.history:
                if h == from_index:
                    new_history.append(to_index)
                elif from_index < h <= to_index:
                    new_history.append(h - 1)
                elif to_index <= h < from_index:
                    new_history.append(h + 1)
                else:
                    new_history.append(h)
            self.history = new_history

            # Rebuild shuffle if active
            if self._is_shuffled:
                self._rebuild_shuffle()
            return True

    def clear(self):
        with self._lock:
            self._tracks.clear()
            self._shuffled_indices.clear()
            self._current_index = -1
            self.history.clear()

    def toggle_shuffle(self):
        with self._lock:
            self._is_shuffled = not self._is_shuffled
            if self._is_shuffled:
                self._rebuild_shuffle()
            else:
                self._shuffled_indices.clear()

    def toggle_repeat(self):
        with self._lock:
            if self._repeat_mode == RepeatMode.OFF:
                self._repeat_mode = RepeatMode.ALL
            elif self._repeat_mode == RepeatMode.ALL:
                self._repeat_mode = RepeatMode.ONE
            else:
                self._repeat_mode = RepeatMode.OFF

    def _rebuild_shuffle(self):
        with self._lock:
            if not self._tracks:
                self._shuffled_indices = []
                return
                
            # Ensure current index is within bounds before rebuilding shuffle
            if self._current_index != -1 and (self._current_index < 0 or self._current_index >= len(self._tracks)):
                self._current_index = -1

            indices = list(range(len(self._tracks)))
            if self._current_index != -1 and self._current_index in indices:
                indices.remove(self._current_index)
                
            random.shuffle(indices)
            
            if self._current_index != -1:
                self._shuffled_indices = [self._current_index] + indices
            else:
                self._shuffled_indices = indices

    def next(self) -> Optional[TrackInfo]:
        with self._lock:
            if not self._tracks:
                return None

            if self._repeat_mode == RepeatMode.ONE and self._current_index != -1:
                # Return current track again
                return self._tracks[self._current_index]

            if self._is_shuffled:
                if not self._shuffled_indices:
                    self._rebuild_shuffle()
                
                # Find where we are in the shuffled array
                try:
                    shuffled_pos = self._shuffled_indices.index(self._current_index)
                except ValueError:
                    shuffled_pos = -1

                if shuffled_pos + 1 < len(self._shuffled_indices):
                    if self._current_index != -1:
                        self.history.append(self._current_index)
                    self._current_index = self._shuffled_indices[shuffled_pos + 1]
                    return self._tracks[self._current_index]
                else:
                    # End of shuffled list
                    if self._repeat_mode == RepeatMode.ALL:
                        self._rebuild_shuffle()
                        if self._current_index != -1:
                            self.history.append(self._current_index)
                        self._current_index = self._shuffled_indices[0]
                        return self._tracks[self._current_index]
                    else:
                        return None
            else:
                if self._current_index + 1 < len(self._tracks):
                    if self._current_index != -1:
                        self.history.append(self._current_index)
                    self._current_index += 1
                    return self._tracks[self._current_index]
                else:
                    if self._repeat_mode == RepeatMode.ALL:
                        if self._current_index != -1:
                            self.history.append(self._current_index)
                        self._current_index = 0
                        return self._tracks[self._current_index]
                    else:
                        return None

    def previous(self) -> Optional[TrackInfo]:
        with self._lock:
            if not self._tracks:
                return None

            if self._repeat_mode == RepeatMode.ONE and self._current_index != -1:
                return self._tracks[self._current_index]

            while self.history:
                idx = self.history.pop()
                if 0 <= idx < len(self._tracks):
                    self._current_index = idx
                    return self._tracks[self._current_index]

            # No history, just go back 1 index (or loop)
            if not self._is_shuffled:
                if 0 <= self._current_index < len(self._tracks):
                    if self._current_index > 0:
                        self._current_index -= 1
                        return self._tracks[self._current_index]
                    elif self._repeat_mode == RepeatMode.ALL:
                        self._current_index = len(self._tracks) - 1
                        return self._tracks[self._current_index]
                else:
                    if self._repeat_mode == RepeatMode.ALL:
                        self._current_index = len(self._tracks) - 1
                        return self._tracks[self._current_index]
            return None

    def current(self) -> Optional[TrackInfo]:
        with self._lock:
            if 0 <= self._current_index < len(self._tracks):
                return self._tracks[self._current_index]
            return None
