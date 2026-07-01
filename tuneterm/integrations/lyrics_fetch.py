import requests
import logging
import urllib.parse
import concurrent.futures

_log = logging.getLogger("tuneterm")

TIMEOUT = 4  # seconds per provider


def _fetch_lrclib(artist: str, title: str):
    """Try LRCLIB API (synced lyrics)."""
    try:
        resp = requests.get(
            "https://lrclib.net/api/get",
            params={"artist_name": artist, "track_name": title},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("syncedLyrics") or data.get("plainLyrics")
    except Exception:
        pass
    return None


def _fetch_lyrics_ovh(artist: str, title: str):
    """Fallback: Lyrics.ovh API."""
    try:
        url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("lyrics")
    except Exception:
        pass
    return None


def _fetch_lyrics_net(artist: str, title: str):
    """Another fallback: lyrist / vercel."""
    try:
        resp = requests.get(
            f"https://lyrist.vercel.app/api/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}",
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("lyrics")
    except Exception:
        pass
    return None


def fetch_lyrics_from_web(artist: str, title: str) -> str:
    """Fetch lyrics from 3 sources IN PARALLEL. Returns first success."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(fn, artist, title): name
            for fn, name in [
                (_fetch_lrclib, "lrclib"),
                (_fetch_lyrics_ovh, "ovh"),
                (_fetch_lyrics_net, "net"),
            ]
        }
        try:
            for future in concurrent.futures.as_completed(futures, timeout=TIMEOUT + 2):
                try:
                    result = future.result()
                    if result:
                        return result
                except Exception:
                    continue
        except concurrent.futures.TimeoutError:
            pass

    _log.warning("[LyricsFetch] Semua sumber gagal untuk %s - %s", artist, title)
    return ""
