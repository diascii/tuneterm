import logging

from textual.containers import Vertical, Horizontal
from textual.widgets import Static
from tuneterm.ui.spinning_art import SpinningArt
from tuneterm.ui.visualizer import Visualizer

_log = logging.getLogger("tuneterm")


class TrackInfoDisplay(Static):
    def update_info(self, title, artist, album):
        self.update(f"[b]{title}[/b]\n{artist}\n{album}")

class NowPlaying(Vertical):
    def compose(self):
        with Horizontal(id="now-playing-top"):
            yield SpinningArt(id="spinning-art")
            with Vertical(id="right-stack"):
                yield TrackInfoDisplay(id="track-info")
                yield Visualizer(id="visualizer")

    def update_track(self, title, artist, album, cover_art_bytes):
        try:
            self.query_one(TrackInfoDisplay).update_info(title, artist, album)
        except Exception as e:
            _log.warning("[NowPlaying] Gagal update info track: %s", e)
        art = self.query_one(SpinningArt)
        art.set_art(cover_art_bytes)
        
    def set_playing(self, is_playing: bool):
        try:
            self.query_one(SpinningArt).is_playing = is_playing
        except Exception as e:
            _log.warning("[NowPlaying] Gagal set playing state: %s", e)
