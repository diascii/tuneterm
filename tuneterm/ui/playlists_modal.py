from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, OptionList, Input, Label, Static
from textual.widgets.option_list import Option
from tuneterm.player.playlists import get_playlists, load_playlist, delete_playlist

class PlaylistsModal(ModalScreen):
    """Modal for managing playlists."""
    
    CSS = """
    PlaylistsModal {
        align: center middle;
        background: $background 50%;
    }
    
    #playlists-dialog {
        width: 60;
        height: 25;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    
    #playlists-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    
    #playlists-list {
        height: 1fr;
        border: solid $primary-darken-2;
    }
    
    #playlists-buttons {
        height: auto;
        margin-top: 1;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="playlists-dialog"):
            yield Label("Playlists Manager", id="playlists-title")
            yield OptionList(id="playlists-list")
            with Horizontal(id="playlists-buttons"):
                yield Button("Load", id="btn-load", variant="primary")
                yield Button("Delete", id="btn-delete", variant="error")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self):
        self._refresh_list()
        
    def _refresh_list(self):
        op_list = self.query_one("#playlists-list", OptionList)
        op_list.clear_options()
        self.playlists = get_playlists()
        for idx, name in enumerate(self.playlists):
            op_list.add_option(Option(name, id=str(idx)))
            
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-cancel":
            self.dismiss()
            return
            
        op_list = self.query_one("#playlists-list", OptionList)
        if op_list.highlighted is None:
            return
            
        name = self.playlists[op_list.highlighted]
        
        if event.button.id == "btn-load":
            tracks = load_playlist(name)
            if hasattr(self.app, 'load_playlist_tracks'):
                self.app.load_playlist_tracks(tracks)
            self.dismiss()
            
        elif event.button.id == "btn-delete":
            delete_playlist(name)
            self._refresh_list()
