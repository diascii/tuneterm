from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Vertical, Horizontal
from tuneterm.utils.config import config
import os

class FirstRunScreen(ModalScreen):
    def compose(self):
        yield Vertical(
            Label("Welcome to TuneTerm!", id="welcome-title"),
            Label("Please enter the path to your Music directory:"),
            Input(placeholder="e.g. D:\\Music", id="music-dir-input"),
            Horizontal(
                Button("Save", variant="success", id="save-btn"),
                id="first-run-buttons"
            ),
            id="first-run-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            inp = self.query_one("#music-dir-input", Input)
            path = inp.value.strip()
            if os.path.isdir(path):
                config.music_dir = path
                config.save()
                self.app.pop_screen()
                # Inform the app to reload with the new directory
                if hasattr(self.app, 'load_music_dir'):
                    self.app.load_music_dir(path)
            else:
                self.notify("Invalid directory path.", severity="error")
