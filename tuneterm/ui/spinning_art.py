import logging
import threading

from textual.reactive import reactive
from textual.widgets import Static
from tuneterm.utils.ascii_art import generate_vinyl_frames

_log = logging.getLogger("tuneterm")


class SpinningArt(Static):
    frames = reactive([])
    current_frame_index = reactive(0)
    is_playing = reactive(False)

    def on_mount(self):
        self.animation_timer = self.set_interval(0.1, self.tick, pause=True)
        self.update("Loading vinyl...")

    def set_art(self, image_bytes: bytes):
        def worker():
            try:
                new_frames = generate_vinyl_frames(image_bytes, width=20, height=10)
                try:
                    self.app.call_from_thread(self.update_frames, new_frames)
                except Exception as e:
                    _log.warning("[SpinningArt] Gagal update frames di main thread (app mungkin sudah cleanup): %s", e)
            except Exception as e:
                _log.warning("[SpinningArt] Gagal generate vinyl frames: %s", e)
                
                # fallback blank frames
                try:
                    new_frames = generate_vinyl_frames(None, width=20, height=10)
                    try:
                        self.app.call_from_thread(self.update_frames, new_frames)
                    except Exception as e:
                        _log.warning("[SpinningArt] Gagal update fallback frames (app mungkin sudah cleanup): %s", e)
                except Exception as e:
                    _log.warning("[SpinningArt] Gagal generate fallback vinyl frames: %s", e)
                    
        threading.Thread(target=worker, daemon=True).start()

    def update_frames(self, new_frames):
        self.frames = new_frames
        self.current_frame_index = 0
        self.render_frame()

    def watch_is_playing(self, is_playing: bool):
        if is_playing:
            self.animation_timer.resume()
        else:
            self.animation_timer.pause()

    def tick(self):
        if self.frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.render_frame()

    def render_frame(self):
        if self.frames:
            from rich.text import Text
            self.update(Text.from_ansi(self.frames[self.current_frame_index]))
