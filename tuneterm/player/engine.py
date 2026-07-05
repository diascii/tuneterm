import vlc
import threading

class VLCAudioEngine:
    def __init__(self):
        # Initialize VLC instance with larger caches to prevent micro-stutters
        # "--no-video" ensures we only deal with audio
        self.instance = vlc.Instance(
            "--no-video",
            "--quiet",
            "--file-caching=3000",
            "--network-caching=3000",
            "--live-caching=3000"
        )
        self.player = self.instance.media_player_new()
        self.lock = threading.RLock()
        
        # State tracking
        self._current_media = None
        self._user_volume = 100
        self.end_reached = False
        
        # Attach events
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self._on_event)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_event)
        
        # Instantiate Equalizer
        from tuneterm.player.equalizer import Equalizer
        self.equalizer = Equalizer(self)

    def _on_event(self, event):
        self.end_reached = True

    def play(self, filepath: str):
        with self.lock:
            self.end_reached = False
            # Langsung play — VLC handles internal state
            self._current_media = self.instance.media_new(filepath)
            self.player.set_media(self._current_media)
            self.player.play()

    def pause(self):
        with self.lock:
            self.player.pause()

    def resume(self):
        with self.lock:
            if not self.is_playing():
                self.player.play()

    def stop(self):
        with self.lock:
            self.player.stop()

    def toggle_pause(self):
        with self.lock:
            if self.is_playing():
                self.pause()
            else:
                self.resume()

    def seek_relative(self, seconds: float):
        current = self.get_position()
        if current >= 0:
            target = current + seconds
            self.seek_absolute(target)

    def seek_absolute(self, seconds: float):
        with self.lock:
            if not self.is_playing():
                return
            # set_time takes milliseconds
            # Need to ensure we don't seek past duration or before 0
            target_ms = int(seconds * 1000)
            target_ms = max(0, target_ms)
            duration_ms = self.player.get_length()
            if duration_ms > 0:
                target_ms = min(target_ms, duration_ms)
            self.player.set_time(target_ms)

    def fade_volume(self, from_v: int, to_v: int, duration: float, steps: int = 10, abort_event=None):
        """Fade volume from `from_v` to `to_v` over `duration` seconds in `steps` steps.
        Harus dipanggil dari background thread (VLC audio_set_volume bisa block)."""
        import time
        for i in range(steps + 1):
            if abort_event and abort_event.is_set():
                return
            progress = i / steps
            vol = int(from_v + (to_v - from_v) * progress)
            vol = max(0, min(100, vol))
            with self.lock:
                self.player.audio_set_volume(vol)
            time.sleep(duration / (steps + 1))
        # Ensure final volume is set
        if not abort_event or not abort_event.is_set():
            with self.lock:
                self.player.audio_set_volume(to_v)

    @property
    def volume(self) -> int:
        return self._user_volume

    @volume.setter
    def volume(self, val: int):
        with self.lock:
            val = max(0, min(100, val))
            self.player.audio_set_volume(val)
            self._user_volume = val

    def set_volume(self, volume: int):
        with self.lock:
            val = max(0, min(100, volume))
            self.player.audio_set_volume(val)
            self._user_volume = val

    def mute(self, state: bool):
        with self.lock:
            self.player.audio_set_mute(1 if state else 0)

    def get_volume(self) -> int:
        return self._user_volume

    def get_position(self) -> float:
        # returns position in seconds, or -1 if no media
        time_ms = self.player.get_time()
        return time_ms / 1000.0 if time_ms >= 0 else 0.0

    def get_duration(self) -> float:
        # returns duration in seconds
        length_ms = self.player.get_length()
        return length_ms / 1000.0 if length_ms > 0 else 0.0

    def is_playing(self) -> bool:
        return self.player.is_playing() == 1

    def set_equalizer(self, vlc_eq):
        with self.lock:
            if self.player:
                self.player.set_equalizer(vlc_eq)

