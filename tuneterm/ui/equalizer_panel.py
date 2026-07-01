from textual.screen import ModalScreen
from textual.widgets import Label, Select, Button
from textual.containers import Vertical, Horizontal
from tuneterm.player.equalizer import PRESETS, EQ_BANDS

# Textual v8 removed the Slider widget. Create a minimal substitute.
try:
    from textual.widgets import Slider
except ImportError:
    from textual.widgets import Static
    from textual.message import Message

    class Slider(Static):
        """Minimal Slider substitute for textual v8 compatibility."""
        class Changed(Message):
            def __init__(self, slider: "Slider", value: int) -> None:
                super().__init__()
                self.slider = slider
                self.value = value

        def __init__(self, min: int = 0, max: int = 100, step: int = 1,
                     value: int = 0, id: str | None = None) -> None:
            super().__init__(id=id)
            self._min = min
            self._max = max
            self._step = step
            self._value = value
            self._mounted = False

        @property
        def value(self) -> int:
            return self._value

        @value.setter
        def value(self, v: int) -> None:
            self._value = max(self._min, min(self._max, v))
            self.update(f"{'█' * (self._value - self._min + 1)}")

class EqualizerPanel(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._updating_ui = False

    def compose(self):
        eq = self.app.engine.equalizer
        with Vertical(id="eq-container"):
            yield Label("Equalizer", id="eq-title")
            
            options = [(k, k) for k in PRESETS.keys()]
            yield Horizontal(
                Label("Preset:"),
                Select(options, value=eq.current_preset, id="eq-preset-select"),
                Button("Reset", id="eq-reset-btn"),
                id="eq-header"
            )
            
            # Preamp Slider
            with Horizontal(classes="eq-slider-row"):
                yield Label(f"Preamp: {eq.preamp:+.1f} dB", id="eq-preamp-label", classes="eq-label")
                yield Slider(min=-20, max=20, step=1, value=int(eq.preamp), id="eq-preamp-slider")

            # 10 frequency bands
            for idx, band_hz in enumerate(EQ_BANDS):
                hz_str = f"{band_hz} Hz" if band_hz < 1000 else f"{band_hz/1000:.1f} kHz"
                val = eq.bands[idx]
                with Horizontal(classes="eq-slider-row"):
                    yield Label(f"{hz_str}: {val:+.1f} dB", id=f"eq-band-label-{idx}", classes="eq-label")
                    yield Slider(min=-20, max=20, step=1, value=int(val), id=f"eq-band-slider-{idx}")
            
            yield Label("Press ESC to close", id="eq-footer")

    def on_mount(self) -> None:
        self.update_sliders()

    def update_sliders(self) -> None:
        self._updating_ui = True
        try:
            eq = self.app.engine.equalizer
            # Update preamp
            preamp_slider = self.query_one("#eq-preamp-slider", Slider)
            preamp_slider.value = int(eq.preamp)
            preamp_label = self.query_one("#eq-preamp-label", Label)
            preamp_label.update(f"Preamp: {eq.preamp:+.1f} dB")
            
            # Update bands
            for idx, band_hz in enumerate(EQ_BANDS):
                val = eq.bands[idx]
                slider = self.query_one(f"#eq-band-slider-{idx}", Slider)
                slider.value = int(val)
                
                hz_str = f"{band_hz} Hz" if band_hz < 1000 else f"{band_hz/1000:.1f} kHz"
                label = self.query_one(f"#eq-band-label-{idx}", Label)
                label.update(f"{hz_str}: {val:+.1f} dB")
        finally:
            self._updating_ui = False

    def on_select_changed(self, event: Select.Changed) -> None:
        if getattr(self, "_updating_ui", False):
            return
            
        if event.select.id == "eq-preset-select":
            preset_name = event.value
            if preset_name:
                self.app.engine.equalizer.apply_preset(preset_name)
                self.update_sliders()

    def on_slider_changed(self, event: Slider.Changed) -> None:
        if getattr(self, "_updating_ui", False):
            return
            
        slider_id = event.slider.id
        val = event.value
        eq = self.app.engine.equalizer
        
        # If it's preamp slider:
        if slider_id == "eq-preamp-slider":
            eq.set_preamp(val)
            label = self.query_one("#eq-preamp-label", Label)
            label.update(f"Preamp: {val:+.1f} dB")
            
        # If it's a band slider:
        elif slider_id and slider_id.startswith("eq-band-slider-"):
            idx = int(slider_id.split("-")[-1])
            eq.set_band(idx, val)
            
            # Update label
            band_hz = EQ_BANDS[idx]
            hz_str = f"{band_hz} Hz" if band_hz < 1000 else f"{band_hz/1000:.1f} kHz"
            label = self.query_one(f"#eq-band-label-{idx}", Label)
            label.update(f"{hz_str}: {val:+.1f} dB")
            
            # Update Select preset dropdown value to Custom
            select = self.query_one("#eq-preset-select", Select)
            if select.value is not None:
                self._updating_ui = True
                try:
                    select.value = None
                finally:
                    self._updating_ui = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "eq-reset-btn":
            eq = self.app.engine.equalizer
            eq.set_preamp(0.0)
            eq.apply_preset("Flat")
            
            # Update the preset dropdown value in UI
            select = self.query_one("#eq-preset-select", Select)
            self._updating_ui = True
            try:
                select.value = "Flat"
            finally:
                self._updating_ui = False
                
            self.update_sliders()

    def action_dismiss(self):
        self.app.pop_screen()

