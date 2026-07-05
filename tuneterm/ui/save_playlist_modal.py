from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from tuneterm.player.playlists import save_playlist

class SavePlaylistModal(ModalScreen):
    """Modal for saving current queue as a playlist."""
    
    CSS = """
    SavePlaylistModal {
        align: center middle;
        background: $background 50%;
    }
    
    #save-playlist-dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    
    #save-playlist-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    
    #save-playlist-input {
        margin-bottom: 1;
    }
    
    #save-playlist-buttons {
        height: auto;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="save-playlist-dialog"):
            yield Label("Save Queue as Playlist", id="save-playlist-title")
            yield Input(placeholder="Playlist name...", id="save-playlist-input")
            with Horizontal(id="save-playlist-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self):
        self.query_one(Input).focus()
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-cancel":
            self.dismiss()
        elif event.button.id == "btn-save":
            self._save()
            
    def on_input_submitted(self, event: Input.Submitted):
        self._save()
        
    def _save(self):
        name = self.query_one(Input).value.strip()
        if not name:
            return
            
        if hasattr(self.app, 'save_current_queue'):
            self.app.save_current_queue(name)
        self.dismiss()
