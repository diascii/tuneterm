import requests
import logging

_log = logging.getLogger("tuneterm")


def _fetch_lrclib(artist: str, title: str) -> str | None:
    """Try LRCLIB API (synced lyrics)."""
    try:
        url = "https://lrclib.net/api/get"
        params = {"artist_name": artist, "track_name": title}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("syncedLyrics"):
                return data["syncedLyrics"]
            elif data.get("plainLyrics"):
                return data["plainLyrics"]
    except Exception as e:
        _log.warning("[LyricsFetch] LRCLIB gagal: %s", e)
    return None


def _fetch_lyrics_ovh(artist: str, title: str) -> str | None:
    """Fallback: Lyrics.ovh API (plain text only)."""
    try:
        import urllib.request, urllib.parse, json
        url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'TuneTerm/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("lyrics"):
                return data["lyrics"]
    except Exception as e:
        _log.warning("[LyricsFetch] Lyrics.ovh gagal: %s", e)
    return None


def fetch_lyrics_from_web(artist: str, title: str) -> str:
    """Fetch lyrics from multiple sources. Tries LRCLIB first, then Lyrics.ovh."""
    result = _fetch_lrclib(artist, title)
    if result:
        return result
    result = _fetch_lyrics_ovh(artist, title)
    if result:
        return result
    _log.warning("[LyricsFetch] Semua sumber lirik gagal untuk %s - %s", artist, title)
    return ""
