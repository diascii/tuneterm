import requests
import logging
import urllib.parse

_log = logging.getLogger("tuneterm")


def _fetch_lrclib(artist: str, title: str):
    """LRCLIB — satu-satunya yang kasih synced LRC.
    Ditunggu lebih lama (10s) biar dapet timestamp real."""
    try:
        resp = requests.get(
            "https://lrclib.net/api/get",
            params={"artist_name": artist, "track_name": title},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("syncedLyrics") or data.get("plainLyrics")
    except Exception as e:
        _log.debug("[LyricsFetch] LRCLIB gagal: %s", e)
    return None


def _fetch_lyrics_ovh(artist: str, title: str):
    """Fallback cepat: Lyrics.ovh (plain text)."""
    try:
        url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("lyrics"):
                return data["lyrics"]
    except Exception:
        pass
    return None


def fetch_lyrics_from_web(artist: str, title: str) -> str:
    """Coba LRCLIB dulu (synced LRC). Kalo gagal, fallback OVH."""
    result = _fetch_lrclib(artist, title)
    if result:
        return result
    result = _fetch_lyrics_ovh(artist, title)
    if result:
        return result
    _log.warning("[LyricsFetch] Semua sumber gagal buat %s - %s", artist, title)
    return ""
