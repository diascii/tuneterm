from textual.widgets import Static
from textual.reactive import reactive
import numpy as np
import threading
import soundcard as sc
import concurrent.futures
import time

class Visualizer(Static):
    mode = reactive("bars")  # "bars", "mirror", "off"
    is_playing = reactive(False)
    
    def on_mount(self):
        self.bands = 32
        self.history = np.zeros(self.bands)
        self.raw_mags = np.zeros(self.bands)
        self.running = True
        self.peak = 0.01  # Running peak for AGC
        
        self._record_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
        
        # UI tick runs at 20fps
        self.timer = self.set_interval(0.05, self.tick, pause=True)
        self.render_bars(self.history)
        
    def on_unmount(self):
        self.running = False
        self._record_executor.shutdown(wait=False)
        if hasattr(self, "audio_thread"):
            self.audio_thread.join(timeout=0.5)
        
    def watch_is_playing(self, playing):
        if playing:
            self.timer.resume()
        else:
            self.timer.pause()
            self.render_bars(np.zeros(self.bands))
            
    def audio_worker(self):
        try:
            import warnings
            
            default_spk = sc.default_speaker()
            mics = sc.all_microphones(include_loopback=True)
            loopback_mic = next((m for m in mics if default_spk.name in m.name and m.isloopback), None)
            
            if not loopback_mic:
                return
                
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with loopback_mic.recorder(samplerate=44100) as mic:
                    while self.running:
                        try:
                            future = self._record_executor.submit(mic.record, numframes=1024)
                            data = future.result(timeout=2.0)  # timeout 2 detik
                        except concurrent.futures.TimeoutError:
                            # Ga ada audio data — skip frame ini
                            self.raw_mags = np.zeros(self.bands)
                            time.sleep(0.05)
                            continue
                        except Exception:
                            self.raw_mags = np.zeros(self.bands)
                            time.sleep(0.05)
                            continue
                        
                        if not self.is_playing or self.mode == "off":
                            self.raw_mags = np.zeros(self.bands)
                            time.sleep(0.1)
                            continue
                            
                        if len(data.shape) > 1:
                            data = np.mean(data, axis=1)
                            
                        # Hanning window to reduce spectral leakage
                        window = np.hanning(len(data))
                        data = data * window
                        
                        # Perform FFT
                        fft_data = np.abs(np.fft.rfft(data))
                        
                        # Adaptive normalization with AGC (running peak)
                        current_peak = np.max(fft_data) if len(fft_data) > 0 else 0.01
                        self.peak = max(current_peak, self.peak * 0.95)  # peak decay
                        self.peak = max(self.peak, 0.01)  # floor

                        if self.peak > 0:
                            fft_data = fft_data / self.peak
                        # Clamp
                        fft_data = np.clip(fft_data, 0, 1.0)
                        
                        # Log-spaced band mapping (more bands for bass, fewer for treble)
                        max_bins = 300
                        band_edges = np.logspace(0, np.log10(max_bins), self.bands + 1).astype(int)
                        band_edges = np.clip(band_edges, 0, len(fft_data) - 1)
                        band_edges[0] = 0
                        
                        mags = np.zeros(self.bands)
                        for i in range(self.bands):
                            start = band_edges[i]
                            end = min(band_edges[i+1] + 1, len(fft_data))
                            if end > start:
                                mags[i] = np.max(fft_data[start:end])  # MAX = more responsive
                            else:
                                mags[i] = 0
                            
                        # Aggressive bass boost
                        mags[0:6] *= 3.0
                        mags[6:10] *= 1.8
                            
                        self.raw_mags = np.clip(mags, 0, 1.0)
                    
        except Exception as e:
            import logging
            logging.getLogger("tuneterm").exception("Visualizer audio capture failed")

    def tick(self):
        # Attack/release envelope: fast rise, slow fall
        raw = self.raw_mags
        attack = 0.6   # fast attack
        release = 0.2  # slow decay
        
        # Per-element: where raw > history, use attack; else use release
        mask = raw > self.history
        alpha = np.where(mask, attack, release)
        self.history = alpha * raw + (1 - alpha) * self.history
        
        self.render_bars(self.history)
        
    def render_bars(self, magnitudes: np.ndarray):
        if self.mode == "off":
            self.update("")
            return
            
        chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        lines = []
        height = 12  # more detail
        
        # Render
        for y in range(height - 1, -1, -1):
            line = ""
            for val in self.history:
                # scale val (assuming max amplitude is ~1.0)
                v = val * height
                if v > y + 1:
                    line += "█"
                elif v > y:
                    idx = int((v - y) * len(chars))
                    idx = max(0, min(len(chars)-1, idx))
                    line += chars[idx]
                else:
                    line += " "
            
            if self.mode == "mirror":
                line = line[::-1] + line
                
            lines.append(line)
            
        # Add basic color later
        self.update("\n".join(lines))
