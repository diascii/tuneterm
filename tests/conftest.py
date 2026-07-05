import sys
import types
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import tempfile
import os
import subprocess
import urllib.request
from pathlib import Path
import json

# 1. Sandbox configuration and database paths
temp_dir = tempfile.TemporaryDirectory()
temp_path = Path(temp_dir.name)

import tuneterm.utils.config
tuneterm.utils.config.CONFIG_DIR = temp_path
tuneterm.utils.config.CONFIG_FILE = temp_path / "config.toml"

import tuneterm.player.library
tuneterm.player.library.DB_PATH = temp_path / "library.db"

# Redirect session file to temp dir — session.py captures CONFIG_DIR at import
# time, so patching CONFIG_DIR alone doesn't isolate it.
import tuneterm.utils.session
tuneterm.utils.session.SESSION_FILE = temp_path / "session.json"

# Reset/initialize config
tuneterm.utils.config.config = tuneterm.utils.config.Config()
tuneterm.utils.config.config.save = MagicMock()

# 2. Mock external dependencies
vlc_module = types.ModuleType("vlc")
class MockEventType:
    MediaPlayerEndReached = 1
    MediaPlayerEncounteredError = 2
    MediaPlayerTimeChanged = 3
vlc_module.EventType = MockEventType

class MockInstance:
    def __init__(self, *args, **kwargs):
        pass
    def media_player_new(self):
        player = MagicMock()
        player._playing = False
        player._volume = 50
        player._time = 0
        player._length = 180000
        player._callbacks = {}
        player._equalizer = None
        player._media = None
        
        player.is_playing = lambda: 1 if player._playing else 0
        def play():
            filepath = player._media.get_mrl() if player._media else ""
            is_local = filepath and not filepath.startswith("http://") and not filepath.startswith("https://")
            does_not_exist = "does_not_exist" in filepath
            if is_local and does_not_exist:
                player._playing = False
                if MockEventType.MediaPlayerEncounteredError in player._callbacks:
                    class Event:
                        pass
                    player._callbacks[MockEventType.MediaPlayerEncounteredError](Event())
                return -1
            player._playing = True
            return 0
        player.play = play
        def pause():
            player._playing = not player._playing
        player.pause = pause
        def stop():
            player._playing = False
            player._time = 0
        player.stop = stop
        player.get_time = lambda: player._time
        def set_time(time_ms):
            player._time = time_ms
            if MockEventType.MediaPlayerTimeChanged in player._callbacks:
                class Event:
                    class u:
                        new_time = time_ms
                player._callbacks[MockEventType.MediaPlayerTimeChanged](Event())
        player.set_time = set_time
        player.get_length = lambda: player._length
        def audio_set_volume(volume):
            player._volume = max(0, min(100, volume))
            return 0
        player.audio_set_volume = audio_set_volume
        player.audio_get_volume = lambda: player._volume
        player.set_equalizer = lambda eq: 0
        player.set_media = lambda media: setattr(player, '_media', media)
        player.get_media = lambda: player._media
        
        event_manager = MagicMock()
        def event_attach(event_type, callback):
            player._callbacks[event_type] = callback
        event_manager.event_attach = event_attach
        player.event_manager.return_value = event_manager
        
        def trigger_event(event_type, event_obj=None):
            if event_type in player._callbacks:
                player._callbacks[event_type](event_obj)
        player.trigger_event = trigger_event
        
        return player

    def media_new(self, filepath):
        media = MagicMock()
        media.get_mrl.return_value = filepath
        return media

vlc_module.Instance = MockInstance
class MockAudioEqualizer:
    def __init__(self):
        self._preamp = 0.0
        self._bands = [0.0] * 10
    def set_preamp(self, value):
        self._preamp = value
    def set_amp_at_index(self, value, index):
        if 0 <= index < 10:
            self._bands[index] = value
vlc_module.AudioEqualizer = MockAudioEqualizer
sys.modules['vlc'] = vlc_module

# Soundcard Mock
soundcard_module = types.ModuleType("soundcard")
class MockSpeaker:
    def __init__(self):
        self.name = "MockSpeaker"
soundcard_module.default_speaker = lambda: MockSpeaker()

class MockMicrophone:
    def __init__(self):
        self.name = "MockSpeaker"
        self.isloopback = True
    def recorder(self, samplerate=44100):
        class RecorderContext:
            def __enter__(self):
                rec = MagicMock()
                # Introduce sleep to prevent high CPU utilization
                def record(numframes=1024):
                    import time
                    time.sleep(0.023)
                    return np.zeros((numframes, 2))
                rec.record = record
                return rec
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return RecorderContext()
soundcard_module.all_microphones = lambda include_loopback=False: [MockMicrophone()]
sys.modules['soundcard'] = soundcard_module

# pypresence Mock
pypresence_module = types.ModuleType("pypresence")
pypresence_module.Presence = MagicMock()
sys.modules['pypresence'] = pypresence_module

# pylast Mock
pylast_module = types.ModuleType("pylast")
pylast_module.LastFMNetwork = MagicMock()
sys.modules['pylast'] = pylast_module

# Mock helper functions
def mock_run(cmd, *args, **kwargs):
    if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "yt-dlp":
        class CompletedProcessMock:
            def __init__(self):
                if "-j" in cmd:
                    self.stdout = json.dumps({
                        "url": "http://example.com/stream.mp3",
                        "title": "Mock YouTube Video",
                        "uploader": "Mock Artist",
                        "thumbnail": "http://example.com/thumb.jpg"
                    })
                else:
                    self.stdout = "http://example.com/stream.mp3\n"
                self.stderr = ""
                self.returncode = 0
        return CompletedProcessMock()
    raise FileNotFoundError()

def mock_urlopen(req, *args, **kwargs):
    url = req.full_url if hasattr(req, 'full_url') else req
    if "example.com" in url or "itunes.apple.com" in url:
        class DummyResponse:
            def read(self):
                return b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DummyResponse()
    import urllib.error
    raise urllib.error.URLError("Network unreachable in tests")

from tuneterm.player.metadata import TrackInfo
def mock_extract_metadata(filepath):
    import os
    filename = os.path.basename(filepath)
    title = os.path.splitext(filename)[0]
    return TrackInfo(
        filepath=filepath,
        title=title,
        artist="Mock Artist",
        album="Mock Album",
        year="2026",
        genre="Mock Genre",
        duration=180.0,
        bitrate=320,
        sample_rate=44100,
        format="MP3",
        cover_art_bytes=b"dummy art bytes",
        thumb_url="http://example.com/thumb.jpg"
    )

@pytest.fixture(autouse=True)
def clean_sys_modules(monkeypatch):
    original_modules = sys.modules.copy()

    sys.modules['vlc'] = vlc_module
    sys.modules['soundcard'] = soundcard_module
    sys.modules['pypresence'] = pypresence_module
    sys.modules['pylast'] = pylast_module

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    import tuneterm.player.metadata
    monkeypatch.setattr(tuneterm.player.metadata, "extract_metadata", mock_extract_metadata)

    # Wipe session file before each test so tests don't bleed into each other.
    # All tests share the same temp_path; a prior test's _save_session() call
    # would pollute subsequent tests via _restore_session() otherwise.
    session_file = tuneterm.utils.session.SESSION_FILE
    if session_file.exists():
        session_file.unlink()

    yield

    # Also clear after the test so teardown saves don't affect the next test
    if session_file.exists():
        session_file.unlink()

    sys.modules.clear()
    sys.modules.update(original_modules)
