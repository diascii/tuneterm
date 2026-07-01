from textual.widgets import Static
from textual.reactive import reactive
from tuneterm.utils.config import config

class StatusBar(Static):
    theme_name = reactive(config.theme)
    track_count = reactive(0)
    
    def on_mount(self):
        self.update_status()
        
    def watch_theme_name(self, _):
        self.update_status()
        
    def watch_track_count(self, _):
        self.update_status()
        
    def update_status(self):
        self.update(f"Theme: {self.theme_name} | Tracks: {self.track_count} | Shuffle: {config.shuffle}")
