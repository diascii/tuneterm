import threading
import logging

_log = logging.getLogger("tuneterm")

class Crossfader:
    def __init__(self, engine):
        self.engine = engine
        self.fade_duration = 2.0  # seconds
        self._active = False

    def crossfade_out(self, on_done=None):
        """Fade out current track volume. Calls on_done when complete."""
        if self._active:
            return
        self._active = True
        def _fade():
            try:
                self.engine.fade_volume(100, 0, self.fade_duration)
                if on_done:
                    on_done()
            except Exception as e:
                _log.warning("[Crossfader] Fade-out error: %s", e)
            finally:
                self._active = False
        t = threading.Thread(target=_fade, daemon=True)
        t.start()

    def crossfade_in(self):
        """Fade in the new track volume."""
        def _fade():
            try:
                self.engine.volume = 0  # start silent
                self.engine.fade_volume(0, 100, self.fade_duration)
            except Exception as e:
                _log.warning("[Crossfader] Fade-in error: %s", e)
        t = threading.Thread(target=_fade, daemon=True)
        t.start()
