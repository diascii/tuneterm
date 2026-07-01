import logging
import time

from pypresence import Presence

_log = logging.getLogger("tuneterm")


class DiscordRPC:
    def __init__(self, client_id="1521277587366613013"):
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        
    def connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
        except Exception as e:
            _log.warning("[DiscordRPC] Gagal connect: %s", e)
            self.connected = False
            
    def update(self, details: str, state: str, large_image: str = None):
        if self.connected and self.rpc:
            try:
                kwargs = {
                    "details": details,
                    "state": state,
                    "large_text": "TuneTerm",
                    "start": time.time()
                }
                if large_image:
                    kwargs["large_image"] = large_image
                    
                self.rpc.update(**kwargs)
            except Exception as e:
                _log.warning("[DiscordRPC] Gagal update presence: %s", e)
                self.connected = False
