import logging
import os
from dataclasses import dataclass
from typing import Optional
import mutagen

_log = logging.getLogger("tuneterm")

@dataclass
class TrackInfo:
    filepath: str
    title: str
    artist: str
    album: str
    year: str
    genre: str
    duration: float
    bitrate: int
    sample_rate: int
    format: str
    cover_art_bytes: Optional[bytes] = None
    thumb_url: Optional[str] = None
    original_url: Optional[str] = None
    is_unresolved: bool = False
    search_query: Optional[str] = None

def extract_metadata(filepath: str) -> TrackInfo:
    filename = os.path.basename(filepath)
    title = os.path.splitext(filename)[0]
    artist = "Unknown Artist"
    album = "Unknown Album"
    year = ""
    genre = ""
    duration = 0.0
    bitrate = 0
    sample_rate = 0
    fmt = "Unknown"

    try:
        audio = mutagen.File(filepath, easy=True)
        if audio is not None:
            # Info
            if hasattr(audio, 'info'):
                duration = getattr(audio.info, 'length', 0.0)
                bitrate = getattr(audio.info, 'bitrate', 0)
                sample_rate = getattr(audio.info, 'sample_rate', 0)
            
            fmt = audio.__class__.__name__

            # Tags (using easy=True where possible)
            if audio.tags is not None:
                title = audio.tags.get('title', [title])[0]
                artist = audio.tags.get('artist', [artist])[0]
                album = audio.tags.get('album', [album])[0]
                year = audio.tags.get('date', audio.tags.get('year', [year]))[0]
                genre = audio.tags.get('genre', [genre])[0]
    except Exception as e:
        _log.debug("[Metadata] Gagal extract metadata untuk %s: %s", filepath, e)

    return TrackInfo(
        filepath=filepath,
        title=str(title),
        artist=str(artist),
        album=str(album),
        year=str(year),
        genre=str(genre),
        duration=float(duration),
        bitrate=int(bitrate),
        sample_rate=int(sample_rate),
        format=str(fmt)
    )

def extract_cover_art(filepath: str) -> Optional[bytes]:
    try:
        audio = mutagen.File(filepath)
        if audio is None or audio.tags is None:
            return None

        # MP3 (ID3)
        if hasattr(audio.tags, 'getall'):
            apic = audio.tags.getall('APIC')
            if apic:
                return apic[0].data

        # FLAC
        if hasattr(audio, 'pictures') and audio.pictures:
            return audio.pictures[0].data
            
        # MP4 / M4A
        if 'covr' in audio.tags:
            return audio.tags['covr'][0]
            
    except Exception as e:
        _log.debug("[Metadata] Gagal extract cover art untuk %s: %s", filepath, e)
        
    return None

import functools
import urllib.request
import urllib.parse
import json

@functools.lru_cache(maxsize=128)
def fetch_itunes_artwork(artist: str, title: str) -> Optional[str]:
    """Fetch and cache high-res album art from iTunes Search API."""
    try:
        query = urllib.parse.quote(f"{artist} {title}")
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            resp = response.read()
        data = json.loads(resp)
        if data['results']:
            # Get 512x512 image instead of 100x100
            return data['results'][0]['artworkUrl100'].replace('100x100bb', '512x512bb')
    except Exception as e:
        _log.warning("[Metadata] Gagal fetch iTunes art: %s", e)
    return None
