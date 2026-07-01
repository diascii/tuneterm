import pytest
import sqlite3
import os
import time
from unittest.mock import MagicMock, patch
from tuneterm.player.library import Library, DB_PATH
from tuneterm.player.playlist import Playlist
from tuneterm.player.metadata import TrackInfo
from tuneterm.ui.lyrics_panel import LyricsPanel
from tuneterm.ui.app import TuneTermApp
from tuneterm.player.equalizer import Equalizer

def test_library_wal_mode_and_conns():
    # Test that library initializes and WAL mode is set
    lib = Library()
    # Check that database exists
    assert os.path.exists(DB_PATH)
    # Check WAL mode
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"

def test_library_scan_directory_background(tmp_path):
    # Test background thread directory scanning
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    (music_dir / "track1.mp3").write_text("dummy")
    (music_dir / "track2.wav").write_text("dummy")
    
    lib = Library()
    lib.scan_directory(str(music_dir))
    
    # Wait up to 1 second for the background thread to finish
    for _ in range(20):
        results = lib.search("")
        if len(results) >= 2:
            break
        time.sleep(0.05)
        
    results = lib.search("")
    assert len(results) >= 2
    paths = [r.filepath for r in results]
    assert str(music_dir / "track1.mp3") in paths
    assert str(music_dir / "track2.wav") in paths

def test_playlist_add_track_info():
    playlist = Playlist()
    track = TrackInfo(
        filepath="search_track.mp3",
        title="Search Track",
        artist="Search Artist",
        album="Search Album",
        year="2026",
        genre="Search Genre",
        duration=200.0,
        bitrate=320,
        sample_rate=44100,
        format="MP3"
    )
    playlist.add_track_info(track)
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "Search Track"
    assert playlist.tracks[0].filepath == "search_track.mp3"

def test_lyrics_panel_lrc_parsing():
    panel = LyricsPanel()
    lrc_content = """[ti:Test Song]
[ar:Test Artist]
[00:00.00] Line 1
[00:05.50] Line 2
[00:10.00] Line 3
"""
    lines = panel.parse_lrc(lrc_content)
    assert len(lines) == 3
    assert lines[0] == (0.0, "Line 1")
    assert lines[1] == (5.5, "Line 2")
    assert lines[2] == (10.0, "Line 3")

def test_lyrics_panel_highlighting_and_viewport():
    panel = LyricsPanel()
    panel.lyrics_lines = [
        (0.0, "Line 1"),
        (5.0, "Line 2"),
        (10.0, "Line 3"),
        (15.0, "Line 4"),
        (20.0, "Line 5"),
    ]
    # At t = 6.0, Line 2 is active
    panel.update_position(6.0)
    # Verify update was called with content containing Line 2
    assert panel.lyrics_lines[1][1] == "Line 2"  # Line 2 exists
    assert panel.lyrics_lines[0][1] == "Line 1"  # Line 1 exists
    
@pytest.mark.asyncio
async def test_app_play_from_search():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        track = TrackInfo(
            filepath="direct_search.mp3",
            title="Direct Search Title",
            artist="Direct Search Artist",
            album="Direct Search Album",
            year="2026",
            genre="Direct",
            duration=120.0,
            bitrate=320,
            sample_rate=44100,
            format="MP3"
        )
        app.play_from_search(track)
        await pilot.pause()
        assert app.playlist.tracks[0].title == "Direct Search Title"

def test_playlist_add_returns_track_info():
    playlist = Playlist()
    track = playlist.add("test_track.mp3")
    assert isinstance(track, TrackInfo)
    assert track.title == "test_track"

    info = TrackInfo(
        filepath="another.mp3",
        title="Another Title",
        artist="Artist",
        album="Album",
        year="2026",
        genre="Genre",
        duration=100.0,
        bitrate=192,
        sample_rate=44100,
        format="MP3"
    )
    returned_info = playlist.add_track_info(info)
    assert returned_info is info

def test_playlist_remove_updates_history_safely():
    playlist = Playlist()
    playlist.add("song0.mp3")
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.add("song3.mp3")
    
    # Simulate playing song 0, 1, 2, 3
    playlist._current_index = 0
    playlist.next()  # current = 1, history = [0]
    playlist.next()  # current = 2, history = [0, 1]
    playlist.next()  # current = 3, history = [0, 1, 2]
    
    assert playlist.history == [0, 1, 2]
    
    # Remove track at index 1 (song1.mp3)
    playlist.remove(1)
    # Indices in history should be:
    # 0 -> 0 (less than 1, unchanged)
    # 1 -> removed
    # 2 -> 1 (greater than 1, decremented)
    assert playlist.history == [0, 1]
    
    # Check that previous works with this history
    prev_track = playlist.previous()  # pops index 1 (which was index 2 originally, song2)
    assert prev_track.title == "song2"
    assert playlist.current_index == 1
    
    prev_track = playlist.previous()  # pops index 0 (song0)
    assert prev_track.title == "song0"
    assert playlist.current_index == 0

def test_playlist_previous_out_of_bounds_safety():
    playlist = Playlist()
    playlist.add("song0.mp3")
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    
    # Navigate: 0 -> 1 -> 2
    playlist._current_index = 0
    playlist.next()  # current = 1, history = [0]
    playlist.next()  # current = 2, history = [0, 1]
    
    assert playlist.history == [0, 1]
    
    # Manually insert an invalid index or mutate history to contain out-of-bounds index
    playlist.history.append(99)  # invalid index
    
    # Calling previous should handle the out-of-bounds 99 safely (discarding/popping it)
    # and pop the next valid one (1)
    prev_track = playlist.previous()
    assert prev_track.title == "song1"
    assert playlist.current_index == 1
