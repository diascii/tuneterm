import json
import logging
from pathlib import Path
from tuneterm.utils.config import CONFIG_DIR

_log = logging.getLogger("tuneterm")

PLAYLISTS_DIR = CONFIG_DIR / "playlists"

def _ensure_dir():
    if not PLAYLISTS_DIR.exists():
        PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)

def get_playlists() -> list[str]:
    _ensure_dir()
    playlists = []
    for f in PLAYLISTS_DIR.glob("*.json"):
        playlists.append(f.stem)
    return sorted(playlists)

def save_playlist(name: str, tracks: list[str]):
    _ensure_dir()
    filepath = PLAYLISTS_DIR / f"{name}.json"
    try:
        data = {"name": name, "tracks": tracks}
        with open(filepath, "w") as f:
            json.dump(data, f)
        _log.info("[Playlists] Saved playlist '%s' with %d tracks.", name, len(tracks))
    except Exception as e:
        _log.warning("[Playlists] Failed to save playlist '%s': %s", name, e)

def load_playlist(name: str) -> list[str]:
    _ensure_dir()
    filepath = PLAYLISTS_DIR / f"{name}.json"
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return data.get("tracks", [])
    except Exception as e:
        _log.warning("[Playlists] Failed to load playlist '%s': %s", name, e)
        return []

def delete_playlist(name: str):
    _ensure_dir()
    filepath = PLAYLISTS_DIR / f"{name}.json"
    if filepath.exists():
        try:
            filepath.unlink()
            _log.info("[Playlists] Deleted playlist '%s'.", name)
        except Exception as e:
            _log.warning("[Playlists] Failed to delete playlist '%s': %s", name, e)

def add_to_playlist(name: str, tracks: list[str]):
    _ensure_dir()
    existing = load_playlist(name)
    # Append avoiding exact adjacent duplicates
    for t in tracks:
        if not existing or existing[-1] != t:
            existing.append(t)
    save_playlist(name, existing)
