import pytest
import subprocess
import urllib.request
import urllib.error
import json
from unittest.mock import MagicMock, patch
from tuneterm.player.playlist import Playlist
from tuneterm.player.streaming import get_youtube_stream_info, get_youtube_audio_url

# ==============================================================================
# Tier 1: URL Streaming Feature Coverage
# ==============================================================================

def test_stream_url_extraction():
    # Mocking subprocess run to return valid JSON output
    mock_json = json.dumps({
        "url": "http://stream.url/audio.mp3",
        "title": "My Stream Title",
        "uploader": "My Stream Artist",
        "thumbnail": "http://stream.url/thumb.jpg"
    })
    
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = mock_json
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        
        info = get_youtube_stream_info("https://youtube.com/watch?v=abcd")
        assert info["url"] == "http://stream.url/audio.mp3"
        assert info["title"] == "My Stream Title"
        assert info["artist"] == "My Stream Artist"
        assert info["thumbnail"] == "http://stream.url/thumb.jpg"

def test_stream_add_url_to_playlist():
    playlist = Playlist()
    
    # We patch get_youtube_stream_info to return controlled info
    with patch("tuneterm.player.playlist.get_youtube_stream_info") as mock_stream_info:
        mock_stream_info.return_value = {
            "url": "https://stream.mp3",
            "title": "Streamed Song",
            "artist": "Streamed Artist",
            "thumbnail": "https://thumb.jpg"
        }
        # Avoid urllib web requests
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"artbytes"
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            track = playlist.add("https://youtube.com/watch?v=abcd")
            assert len(playlist.tracks) == 1
            assert track.title == "Streamed Song"
            assert track.artist == "Streamed Artist"
            assert track.filepath == "https://stream.mp3"
            assert track.cover_art_bytes == b"artbytes"

def test_stream_play_url():
    from tuneterm.player.engine import VLCAudioEngine
    engine = VLCAudioEngine()
    engine.play("https://stream.mp3")
    assert engine.is_playing() is True
    assert engine.player.get_media().get_mrl() == "https://stream.mp3"

def test_stream_thumbnail_download():
    playlist = Playlist()
    
    # Verify thumbnail fetching calls urlopen and parses bytes
    with patch("tuneterm.player.playlist.get_youtube_stream_info") as mock_stream_info:
        mock_stream_info.return_value = {
            "url": "https://stream.mp3",
            "title": "Streamed Song",
            "artist": "Streamed Artist",
            "thumbnail": "https://thumb.jpg"
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"mocked image bytes"
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            track = playlist.add("https://youtube.com/watch?v=xyz")
            assert track.cover_art_bytes == b"mocked image bytes"
            mock_urlopen.assert_called_once()

def test_stream_fallback_parsing():
    # If the standard JSON extraction fails, get_youtube_audio_url falls back to -g
    with patch("subprocess.run") as mock_run:
        def side_effect(cmd, *args, **kwargs):
            mock_proc = MagicMock()
            if "-j" in cmd:
                # -j fails
                raise subprocess.CalledProcessError(1, cmd)
            elif "-g" in cmd:
                # -g succeeds
                mock_proc.stdout = "https://fallback.stream.url/audio.mp3\n"
                mock_proc.stderr = ""
                mock_proc.returncode = 0
                return mock_proc
            raise ValueError("Unexpected command")
            
        mock_run.side_effect = side_effect
        url = get_youtube_audio_url("https://youtube.com/watch?v=fallback")
        assert url == "https://fallback.stream.url/audio.mp3"


# ==============================================================================
# Tier 2: URL Streaming Boundary & Corner Cases
# ==============================================================================

def test_stream_malformed_empty_urls():
    playlist = Playlist()
    
    # Adding a completely malformed / empty URL
    with patch("tuneterm.player.playlist.get_youtube_stream_info") as mock_stream_info:
        # returns empty dict for malformed url
        mock_stream_info.return_value = {}
        
        track = playlist.add("https://malformed_url")
        assert track.filepath == "https://malformed_url"
        assert track.title == "Streaming Audio"
        assert track.artist == "https://malformed_url"

def test_stream_network_timeout():
    # Mocking subprocess run timing out
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["yt-dlp"], 5)):
        info = get_youtube_stream_info("https://youtube.com/watch?v=timeout")
        assert info == {}

def test_stream_youtube_no_audio():
    # Mocking yt-dlp returning valid json but without a 'url' key
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = json.dumps({
            "title": "No Audio Video",
            "uploader": "Uploader"
        })
        mock_proc.stderr = ""
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        
        url = get_youtube_audio_url("https://youtube.com/watch?v=noaudio")
        assert url == ""

def test_stream_ytdlp_missing():
    # yt-dlp not installed on system (FileNotFoundError)
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        info = get_youtube_stream_info("https://youtube.com/watch?v=noytdlp")
        assert info == {}

def test_stream_download_malformed_cover_art():
    playlist = Playlist()
    
    with patch("tuneterm.player.playlist.get_youtube_stream_info") as mock_stream_info:
        mock_stream_info.return_value = {
            "url": "https://stream.mp3",
            "title": "Song",
            "thumbnail": "https://malformed-image-url.jpg"
        }
        # Mock urlopen throwing an HTTP/URL error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Malformed image bytes")):
            track = playlist.add("https://youtube.com/watch?v=art_fail")
            assert track.cover_art_bytes is None
