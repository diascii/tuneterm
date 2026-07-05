import logging
import subprocess

import json

_log = logging.getLogger("tuneterm")


def get_youtube_stream_info(youtube_url: str) -> dict:
    try:
        cmd = ["yt-dlp", "--no-warnings", "--no-playlist", "-f", "bestaudio", "-j", youtube_url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        data = json.loads(result.stdout.strip())
        if not data.get("url"):
            return {}
        return {
            "url": data["url"],
            "title": data.get("title", "Streaming Audio"),
            "artist": data.get("uploader", youtube_url),
            "thumbnail": data.get("thumbnail", "")
        }
    except subprocess.TimeoutExpired:
        _log.warning("[Streaming] Timeout saat get youtube stream info untuk %s", youtube_url)
        return {}
    except Exception as e:
        _log.warning("[Streaming] Gagal get youtube stream info untuk %s: %s", youtube_url, e)
        return {}

def get_youtube_audio_url(youtube_url: str) -> str:
    """Uses yt-dlp to extract the raw audio stream URL from a YouTube video."""
    info = get_youtube_stream_info(youtube_url)
    if info and info.get("url"):
        return info["url"]
    
    # Fallback to direct parsing if -j fails for some reason
    try:
        cmd = ["yt-dlp", "--no-warnings", "--no-playlist", "-x", "-g", youtube_url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                return line
        return ""
    except subprocess.TimeoutExpired:
        _log.warning("[Streaming] Timeout saat get youtube audio URL fallback untuk %s", youtube_url)
        return ""
    except Exception as e:
        _log.warning("[Streaming] Gagal get youtube audio URL fallback untuk %s: %s", youtube_url, e)
        return ""
