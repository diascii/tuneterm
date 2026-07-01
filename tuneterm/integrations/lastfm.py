import logging

import pylast

_log = logging.getLogger("tuneterm")


class LastFMScrobbler:
    def __init__(self):
        self.network = None
        
    def update_now_playing(self, artist: str, title: str):
        if self.network:
            try:
                self.network.update_now_playing(artist=artist, title=title)
            except Exception as e:
                _log.warning("[LastFM] Gagal update now playing: %s", e)
                
    def scrobble(self, artist: str, title: str, timestamp: int):
        if self.network:
            try:
                self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
            except Exception as e:
                _log.warning("[LastFM] Gagal scrobble: %s", e)
