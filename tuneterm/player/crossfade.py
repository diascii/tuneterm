import threading
import logging

_log = logging.getLogger("tuneterm")

class Crossfader:
    def __init__(self, engine):
        self.engine = engine
        self.fade_duration = 2.0  # seconds
        self._active = False
        self._target_volume = None

    def crossfade_out(self, on_done=None):
        """Fade out current track volume. Calls on_done when complete."""
        if self._active:
            return
        self._active = True
        self._target_volume = self.engine.get_volume()
        
        def _fade():
            try:
                self.engine.fade_volume(self._target_volume, 0, self.fade_duration)
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
        # Use saved target volume from fade out, or current engine volume if it wasn't saved
        target = self._target_volume if self._target_volume is not None else self.engine.get_volume()
        self._target_volume = None # reset
        
        def _fade():
            try:
                self.engine.volume = 0  # start silent
                self.engine.fade_volume(0, target, self.fade_duration)
            except Exception as e:
                _log.warning("[Crossfader] Fade-in error: %s", e)
        t = threading.Thread(target=_fade, daemon=True)
        t.start()
