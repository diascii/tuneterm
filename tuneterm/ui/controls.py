from textual.widgets import Static
from textual import events
from textual.message import Message
from textual.reactive import reactive

def format_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

class PlaybackControls(Static):
    position = reactive(0.0)
    duration = reactive(0.0)
    is_playing = reactive(False)
    shuffle = reactive(False)
    repeat = reactive("OFF")
    
    class SeekMessage(Message):
        def __init__(self, position: float) -> None:
            self.position = position
            super().__init__()

    class ToggleShuffleMessage(Message):
        pass

    class ToggleRepeatMessage(Message):
        pass

    def on_mount(self):
        self.update_display()
        
    def watch_position(self, pos):
        self.update_display()
        
    def watch_duration(self, dur):
        self.update_display()
        
    def watch_is_playing(self, playing):
        self.update_display()

    def watch_shuffle(self, shuf):
        self.update_display()

    def watch_repeat(self, rep):
        self.update_display()

    def update_display(self):
        status = "▶" if self.is_playing else "⏸"
        pos_str = format_time(self.position)
        dur_str = format_time(self.duration)
        
        shuf_icon = "[b green]Shuf: ON[/b green]" if self.shuffle else "[grey50]Shuf: OFF[/grey50]"
        
        if self.repeat == "OFF":
            rep_icon = "[grey50]Rep: OFF[/grey50]"
        elif self.repeat == "ONE":
            rep_icon = "[b green]Rep: ONE[/b green]"
        else:
            rep_icon = "[b green]Rep: ALL[/b green]"
        
        # Calculate progress bar width based on terminal width minus text length
        width = self.size.width if self.size.width > 0 else 80
        # "Shuf: OFF" is 9 chars, "Rep: ALL" is 8 chars. Plus spacing = ~20 chars.
        text_len = len(f" {status} {pos_str} / {dur_str} ") + 20
        bar_width = max(10, width - text_len - 4)
        
        # Store for click calculations
        self._bar_start = len(f" {status}  {pos_str} ")
        self._bar_width = bar_width
        
        progress = 0
        if self.duration > 0:
            progress = self.position / self.duration
            
        filled = int(progress * bar_width)
        empty = bar_width - filled
        
        bar = f"[cyan]{'━' * filled}[/cyan][grey37]{'━' * empty}[/grey37]"
        
        text = f" {status}  {pos_str} {bar} {dur_str}  {shuf_icon}  {rep_icon} "
        self.update(text)

    def on_click(self, event: events.Click) -> None:
        if self.duration > 0 and self.size.width > 0:
            # Check if clicked on the rightmost edge where text buttons are (last 20 characters)
            if event.x >= self.size.width - 20:
                if event.x < self.size.width - 10:
                    self.post_message(self.ToggleShuffleMessage())
                else:
                    self.post_message(self.ToggleRepeatMessage())
                return
                
            # Accurately map the click X coordinate within the actual progress bar
            if hasattr(self, "_bar_start") and hasattr(self, "_bar_width"):
                if event.x >= self._bar_start and event.x <= self._bar_start + self._bar_width:
                    percent = (event.x - self._bar_start) / self._bar_width
                    percent = max(0.0, min(1.0, percent))
                    new_pos = percent * self.duration
                    self.post_message(self.SeekMessage(new_pos))

