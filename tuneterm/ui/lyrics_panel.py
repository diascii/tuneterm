import logging
import os
import re
from textual.widgets import Static
from tuneterm.integrations.lyrics_fetch import fetch_lyrics_from_web

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

    def update_lyrics(self, track_path: str, artist: str = "", title: str = ""):
        lrc_path = os.path.splitext(track_path)[0] + ".lrc"
        if os.path.exists(lrc_path):
            try:
                with open(lrc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.lyrics_lines = self.parse_lrc(content)
                if not self.lyrics_lines:
                    self.update("Lyrics format error.")
                else:
                    self.update_position(0.0)
            except Exception as e:
                _log.warning("[LyricsPanel] Gagal load LRC file %s: %s", lrc_path, e)
                self.lyrics_lines = []
                self.update("Lyrics format error.")
        elif artist and title:
            # No local .lrc file — try fetching from web
            self._fetch_and_display_web_lyrics(artist, title)
        else:
            self.lyrics_lines = []
            self.update("No lyrics found.")

    def _fetch_and_display_web_lyrics(self, artist: str, title: str):
        """Fetch lyrics from LRCLIB and display them."""
        try:
            content = fetch_lyrics_from_web(artist, title)
            if not content:
                self.lyrics_lines = []
                self.update("No lyrics found.")
                return

            # Check if content is LRC-synced (has timestamps) or plain text
            if re.search(r'\[\d+:\d+(?:\.\d+)?\]', content):
                self.lyrics_lines = self.parse_lrc(content)
                if self.lyrics_lines:
                    self.update_position(0.0)
                else:
                    self.lyrics_lines = []
                    self.update("Lyrics format error.")
            else:
                # Plain text — create synthetic timestamps (one line per second)
                plain_lines = [l.strip() for l in content.splitlines() if l.strip()]
                if plain_lines:
                    self.lyrics_lines = [(float(i), line) for i, line in enumerate(plain_lines)]
                    self.update_position(0.0)
                else:
                    self.lyrics_lines = []
                    self.update("No lyrics found.")
        except Exception as e:
            _log.warning("[LyricsPanel] Gagal fetch web lyrics: %s", e)
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
        half = viewport_height // 2
        
        center_idx = active_idx if active_idx != -1 else 0
        start_idx = max(0, center_idx - half)
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

