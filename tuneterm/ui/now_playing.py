import logging

from textual.containers import Vertical, Horizontal
from textual.widgets import Static
from tuneterm.ui.spinning_art import SpinningArt
from tuneterm.ui.visualizer import Visualizer

_log = logging.getLogger("tuneterm")


class TrackInfoDisplay(Static):
    def update_info(self, track):
        if not track:
            return
            
        lines = [
            f"[b]{track.title}[/b]",
            f"{track.artist}",
            f"[grey70]{track.album}[/grey70]"
        ]
        
        # Build metadata row
        meta = []
        if getattr(track, 'year', None):
            meta.append(track.year)
        if getattr(track, 'format', None):
            meta.append(track.format)
        if getattr(track, 'bitrate', 0):
            meta.append(f"{track.bitrate}kbps")
        if getattr(track, 'sample_rate', 0):
            meta.append(f"{track.sample_rate/1000:g}kHz")
            
        if meta:
            lines.append(f"[dim cyan]{' · '.join(meta)}[/dim cyan]")
            
        self.update("\n".join(lines))

class NowPlaying(Vertical):
    def compose(self):
        with Horizontal(id="now-playing-top"):
            yield SpinningArt(id="spinning-art")
            with Vertical(id="right-stack"):
                yield TrackInfoDisplay(id="track-info")
                yield Visualizer(id="visualizer")

    def update_track(self, track, cover_art_bytes):
        try:
            self.query_one(TrackInfoDisplay).update_info(track)
        except Exception as e:
            _log.warning("[NowPlaying] Gagal update info track: %s", e)
        art = self.query_one(SpinningArt)
        art.set_art(cover_art_bytes)
        
    def set_playing(self, is_playing: bool):
        try:
            self.query_one(SpinningArt).is_playing = is_playing
        except Exception as e:
            _log.warning("[NowPlaying] Gagal set playing state: %s", e)
