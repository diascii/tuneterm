from textual.widgets import Static
from textual.reactive import reactive

class StatusBar(Static):
    theme_name = reactive("nord")
    track_count = reactive(0)
    shuffle = reactive(False)
    repeat = reactive("OFF")
    
    def watch_theme_name(self, _):
        self.update_status()
        
    def watch_track_count(self, _):
        self.update_status()
        
    def watch_shuffle(self, _):
        self.update_status()
        
    def watch_repeat(self, _):
        self.update_status()
        
    def update_status(self):
        shuf = "[green]ON[/]" if self.shuffle else "[grey]OFF[/]"
        self.update(f"Theme: [bold]{self.theme_name}[/] | Tracks: {self.track_count} | Shuffle: {shuf} | Repeat: {self.repeat}")
