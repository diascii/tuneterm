from textual.screen import ModalScreen
from textual.widgets import Label, Markdown
from textual.containers import Vertical

HELP_TEXT = """
# Keybindings
- `Space`: Play / Pause
- `n`: Next track
- `p`: Previous track
- `Tab`: Focus file browser / queue
- `h` or `Space` (on folder): Toggle folder expand/collapse
- `l` or `Enter` (on file): Play selected file
- `Right`: Seek +10s
- `Left`: Seek -10s
- `s`: Toggle Shuffle
- `r`: Toggle Repeat
- `t`: Cycle Theme
- `b`: Toggle browser panel
- `u`: Add URL
- `o`: Open Folder
- `/`: Open Search
- `e`: Toggle Equalizer
- `?`: Show Help
- `q`: Quit
"""

class HelpModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Dismiss")]
    
    def compose(self):
        with Vertical(id="help-container"):
            yield Markdown(HELP_TEXT)
            yield Label("Press ESC to close", id="help-footer")
            
    def action_dismiss(self):
        self.app.pop_screen()
