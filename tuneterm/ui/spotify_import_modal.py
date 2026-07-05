from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.containers import Vertical, Horizontal
from typing import List, Dict

class SpotifyImportModal(ModalScreen[str]):
    """Modal to ask whether to Append or Replace queue with Spotify Playlist/Album."""

    def __init__(self, track_count: int, **kwargs):
        super().__init__(**kwargs)
        self.track_count = track_count

    def compose(self):
        with Vertical(id="spotify-import-container", classes="modal-container"):
            yield Label(f"Spotify Detected: {self.track_count} tracks", id="spotify-import-label", classes="modal-title")
            yield Label("What would you like to do with your current queue?", classes="modal-subtitle")
            with Horizontal(classes="modal-buttons"):
                yield Button("Append", id="append-btn", variant="primary")
                yield Button("Replace", id="replace-btn", variant="error")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "append-btn":
            self.dismiss("append")
        elif btn_id == "replace-btn":
            self.dismiss("replace")
        else:
            self.dismiss("cancel")
