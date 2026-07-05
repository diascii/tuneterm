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

    def cancel(self):
        """Immediately abort any running fade threads."""
        self._abort_event.set()
        if self._fade_thread and self._fade_thread.is_alive():
            self._fade_thread.join(timeout=0.5)
        self._abort_event.clear()

    def crossfade_out(self, on_done=None):
        """Fade out current track volume. Calls on_done when complete."""
        self.cancel()
        
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
        self.cancel()
        
        target = self._target_volume if self._target_volume is not None else self.engine.get_volume()
        self._target_volume = None # reset
        
        def _fade():
            try:
                # Wait for VLC to fully initialize the audio output sink
                import time
                _log.info(f"[Crossfader] _fade thread started, waiting for is_playing. Target: {target}")
                wait_start = time.time()
                while not self.engine.is_playing():
                    if self._abort_event.is_set():
                        _log.info("[Crossfader] _fade aborted during wait.")
                        return
                    if time.time() - wait_start > 10.0:
                        _log.warning("[Crossfader] Timeout waiting for is_playing()! Unmuting anyway.")
                        break
                    time.sleep(0.01)

                _log.info("[Crossfader] is_playing is True, waiting for volume to hit 0.")
                
                # We must repeatedly tell it to go to 0 until the audio sink accepts it
                wait_start = time.time()
                while True:
                    if self._abort_event.is_set():
                        _log.info("[Crossfader] _fade aborted during volume zeroing wait.")
                        return
                    if time.time() - wait_start > 1.0:
                        _log.warning("[Crossfader] Timeout waiting for volume to hit 0! Unmuting anyway to prevent silence.")
                        with self.engine.lock:
                            self.engine.player.audio_set_volume(0)
                            self.engine.mute(False)
                        break
                        
                    with self.engine.lock:
                        self.engine.player.audio_set_volume(0)
                        if self.engine.player.audio_get_volume() == 0:
                            self.engine.mute(False)
                            break
                    time.sleep(0.01)
                
                _log.info("[Crossfader] Volume is definitively 0, unmuted. Starting fade.")
                self.engine.fade_volume(0, target, self.fade_duration, abort_event=self._abort_event)
                _log.info("[Crossfader] fade complete.")
            except Exception as e:
                _log.warning("[Crossfader] Fade-in error: %s", e)

        self._fade_thread = threading.Thread(target=_fade, daemon=True)
        self._fade_thread.start()
