import json
import logging
from tuneterm.utils.config import CONFIG_DIR

_log = logging.getLogger("tuneterm")

SESSION_FILE = CONFIG_DIR / "session.json"

def save_session(current_track_path: str, position: float, queue: list[str],
                  music_dir: str = ""):
    data = {
        "current_track": current_track_path,
        "position": position,
        "queue": queue,
        "music_dir": music_dir,
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)

def load_session() -> dict:
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            _log.warning("[Session] Gagal load session: %s", e)
    return {}
