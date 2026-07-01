import logging
import os
import re
from textual.widgets import Static

_log = logging.getLogger("tuneterm")

class LyricsPanel(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lyrics_lines: list[tuple[float, str]] = []

    def parse_lrc(self, content: str) -> list[tuple[float, str]]:
        lines = []
        pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\]')
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            matches = list(pattern.finditer(line))
            if not matches:
                continue
            last_match = matches[-1]
            text = line[last_match.end():].strip()
            for m in matches:
                minutes = int(m.group(1))
                seconds = float(m.group(2))
                timestamp = minutes * 60 + seconds
                lines.append((timestamp, text))
        lines.sort(key=lambda x: x[0])
        return lines

    def try_load_local_lrc(self, track_path: str) -> bool:
        """Load local .lrc file if exists. Returns True if loaded."""
        lrc_path = os.path.splitext(track_path)[0] + ".lrc"
        if not os.path.exists(lrc_path):
            return False
        try:
            with open(lrc_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.lyrics_lines = self.parse_lrc(content)
            if self.lyrics_lines:
                self.update_position(0.0)
                return True
            self.update("Lyrics format error.")
        except Exception as e:
            _log.warning("[LyricsPanel] Gagal load LRC %s: %s", lrc_path, e)
            self.lyrics_lines = []
            self.update("Lyrics format error.")
        return True  # file exists, attempted load

    def display_web_lyrics(self, content: str):
        """Display fetched web lyrics (called from main thread)."""
        if not content:
            self.lyrics_lines = []
            self.update("No lyrics found.")
            return
        if re.search(r'\[\d+:\d+(?:\.\d+)?\]', content):
            self.lyrics_lines = self.parse_lrc(content)
        else:
            plain = [l.strip() for l in content.splitlines() if l.strip()]
            self.lyrics_lines = [(float(i), l) for i, l in enumerate(plain)]
        if self.lyrics_lines:
            self.update_position(0.0)
        else:
            self.lyrics_lines = []
            self.update("No lyrics found.")

    def update_position(self, current_time: float):
        if not self.lyrics_lines:
            return
            
        active_idx = -1
        for i, (ts, text) in enumerate(self.lyrics_lines):
            if ts <= current_time:
                active_idx = i
            else:
                break
                
        viewport_height = 11
        offset = 2  # active line positioned at row 3 (0-indexed: 2)
        
        center_idx = active_idx if active_idx != -1 else 0
        start_idx = max(0, center_idx - offset)
        end_idx = min(len(self.lyrics_lines), start_idx + viewport_height)
        
        if end_idx - start_idx < viewport_height:
            start_idx = max(0, end_idx - viewport_height)
            
        lines_to_render = []
        for i in range(start_idx, end_idx):
            ts, text = self.lyrics_lines[i]
            if i == active_idx:
                lines_to_render.append(f"[bold green]➔ {text}[/bold green]")
            else:
                lines_to_render.append(f"[grey]{text}[/grey]")
                
        self.update("\n".join(lines_to_render))

