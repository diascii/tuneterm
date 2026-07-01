import vlc

EQ_BANDS = [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

PRESETS = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [8, 4, -4, -8, -3, 4, 8, 11, 11, 11],
    "Pop": [-1, 4, 7, 8, 5, -1, -2, -2, -1, -1],
    "Jazz": [0, 0, 0, 3, 3, 3, 0, 3, 4, 5],
    "Classical": [0, 0, 0, 0, 0, 0, -7, -7, -7, -9],
    "Bass Boost": [12, 11, 10, 5, 0, 0, 0, 0, 0, 0]
}

class Equalizer:
    def __init__(self, engine):
        self.engine = engine
        self.vlc_eq = vlc.AudioEqualizer()
        self.current_preset = "Flat"
        self.bands = [0.0] * 10
        self.preamp = 0.0
        self.apply_preset("Flat")

    def apply_preset(self, name: str):
        if name in PRESETS:
            self.current_preset = name
            self.bands = [float(v) for v in PRESETS[name]]
            self._update_vlc()

    def set_band(self, index: int, value: float):
        if 0 <= index < 10:
            self.bands[index] = max(-20.0, min(20.0, value))
            self.current_preset = "Custom"
            self._update_vlc()

    def set_preamp(self, value: float):
        self.preamp = max(-20.0, min(20.0, value))
        self._update_vlc()

    def _update_vlc(self):
        self.vlc_eq.set_preamp(self.preamp)
        for i in range(10):
            self.vlc_eq.set_amp_at_index(self.bands[i], i)
        
        if hasattr(self.engine, 'set_equalizer'):
            self.engine.set_equalizer(self.vlc_eq)
        elif self.engine.player:
            self.engine.player.set_equalizer(self.vlc_eq)
