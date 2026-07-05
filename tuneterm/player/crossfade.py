import threading
import logging

_log = logging.getLogger("tuneterm")

class Crossfader:
    def __init__(self, engine):
        self.engine = engine
        self.fade_duration = 2.0  # seconds
        self._fade_thread = None
        self._abort_event = threading.Event()
        self._target_volume = None

    def crossfade_out(self, on_done=None):
        """Fade out current track volume. Calls on_done when complete."""
        self._abort_event.set()
        if self._fade_thread and self._fade_thread.is_alive():
            self._fade_thread.join(timeout=0.5)

        self._abort_event.clear()
        
        if self._target_volume is None:
            self._target_volume = self.engine.get_volume()

        def _fade():
            try:
                self.engine.fade_volume(self.engine.get_volume(), 0, self.fade_duration, abort_event=self._abort_event)
                if not self._abort_event.is_set() and on_done:
                    on_done()
            except Exception as e:
                _log.warning("[Crossfader] Fade-out error: %s", e)

        self._fade_thread = threading.Thread(target=_fade, daemon=True)
        self._fade_thread.start()

    def crossfade_in(self):
        """Fade in the new track volume."""
        self._abort_event.set()
        if self._fade_thread and self._fade_thread.is_alive():
            self._fade_thread.join(timeout=0.5)

        self._abort_event.clear()
        
        target = self._target_volume if self._target_volume is not None else self.engine.get_volume()
        self._target_volume = None # reset
        
        def _fade():
            try:
                self.engine.volume = 0  # start silent
                self.engine.fade_volume(0, target, self.fade_duration, abort_event=self._abort_event)
            except Exception as e:
                _log.warning("[Crossfader] Fade-in error: %s", e)

        self._fade_thread = threading.Thread(target=_fade, daemon=True)
        self._fade_thread.start()
