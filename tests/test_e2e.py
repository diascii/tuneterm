import pytest
import os
import sys
import tempfile
import time
import shutil
import json
import urllib.request
import subprocess
from pathlib import Path
import threading
from unittest.mock import MagicMock, patch

import numpy as np

# Import under test
from tuneterm.player.engine import VLCAudioEngine
from tuneterm.player.playlist import Playlist, RepeatMode
from tuneterm.player.library import Library
from tuneterm.player.metadata import TrackInfo
from tuneterm.player.equalizer import Equalizer, PRESETS
from tuneterm.utils.config import Config
import tuneterm.utils.config
from tuneterm.ui.app import TuneTermApp
from tuneterm.ui.file_browser import FileBrowser
from tuneterm.ui.track_list import TrackList
from tuneterm.ui.now_playing import NowPlaying
from tuneterm.ui.controls import PlaybackControls, format_time
from tuneterm.ui.spinning_art import SpinningArt
from tuneterm.ui.visualizer import Visualizer
from tuneterm.ui.add_url_modal import AddUrlModal
from tuneterm.ui.search_modal import SearchModal
from tuneterm.ui.first_run import FirstRunScreen
from tuneterm.ui.help_modal import HelpModal

# ==============================================================================
# TIER 1: Feature Coverage (28 tests)
# ==============================================================================

def test_playback_engine_init():
    engine = VLCAudioEngine()
    assert engine.player is not None
    assert engine._current_media is None


def test_playback_engine_play():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    assert engine.is_playing() is True


def test_playback_engine_pause():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.pause()
    assert engine.is_playing() is False


def test_playback_engine_resume():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.pause()
    engine.resume()
    assert engine.is_playing() is True


def test_playback_engine_stop():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.stop()
    assert engine.is_playing() is False
    assert engine.get_position() == 0.0


def test_playback_engine_toggle_pause():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.toggle_pause()
    assert engine.is_playing() is False
    engine.toggle_pause()
    assert engine.is_playing() is True


def test_playback_engine_volume_set():
    engine = VLCAudioEngine()
    engine.set_volume(75)
    assert engine.get_volume() == 75


def test_playback_engine_volume_get():
    engine = VLCAudioEngine()
    engine.set_volume(40)
    assert engine.get_volume() == 40


def test_playback_engine_get_position():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.seek_absolute(12.5)
    assert engine.get_position() == 12.5


def test_playback_engine_get_duration():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    assert engine.get_duration() == 180.0


def test_seeking_absolute():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.seek_absolute(50.0)
    assert engine.get_position() == 50.0


def test_seeking_relative_forward():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.seek_absolute(10.0)
    engine.seek_relative(15.0)
    assert engine.get_position() == 25.0


def test_seeking_relative_backward():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.seek_absolute(50.0)
    engine.seek_relative(-20.0)
    assert engine.get_position() == 30.0


def test_seeking_duration_mapping():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.player._length = 240000
    assert engine.get_duration() == 240.0


def test_seeking_position_mapping():
    engine = VLCAudioEngine()
    engine.play("dummy.mp3")
    engine.player._time = 90000
    assert engine.get_position() == 90.0


def test_playlist_add():
    playlist = Playlist()
    playlist.add("song1.mp3")
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "song1"


def test_playlist_remove():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.remove(0)
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "song2"


def test_playlist_clear():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.clear()
    assert len(playlist.tracks) == 0


def test_playlist_toggle_shuffle():
    playlist = Playlist()
    assert playlist.is_shuffled is False
    playlist.toggle_shuffle()
    assert playlist.is_shuffled is True


def test_playlist_toggle_repeat():
    playlist = Playlist()
    assert playlist.repeat_mode == RepeatMode.OFF
    playlist.toggle_repeat()
    assert playlist.repeat_mode == RepeatMode.ALL
    playlist.toggle_repeat()
    assert playlist.repeat_mode == RepeatMode.ONE
    playlist.toggle_repeat()
    assert playlist.repeat_mode == RepeatMode.OFF


def test_playlist_navigation_next():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    track = playlist.next()
    assert track.title == "song1"
    track = playlist.next()
    assert track.title == "song2"


def test_playlist_navigation_previous():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.next()  # song1
    playlist.next()  # song2
    track = playlist.previous()
    assert track.title == "song1"


def test_stream_url_extraction():
    from tuneterm.player.streaming import get_youtube_stream_info
    info = get_youtube_stream_info("https://youtube.com/watch?v=123")
    assert info["url"] == "http://example.com/stream.mp3"
    assert info["title"] == "Mock YouTube Video"


def test_stream_add_url_to_playlist():
    playlist = Playlist()
    playlist.add("https://youtube.com/watch?v=123")
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "Mock YouTube Video"
    assert playlist.tracks[0].format == "Stream"


@pytest.mark.asyncio
async def test_ui_file_browser_load():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        browser = app.query_one(FileBrowser)
        temp_dir = tempfile.TemporaryDirectory()
        browser.load_directory(temp_dir.name)
        assert str(browser.path) == temp_dir.name
        temp_dir.cleanup()


@pytest.mark.asyncio
async def test_ui_track_list_render():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        track_list = app.query_one(TrackList)
        track_list.add_row("Title", "Artist", "Album", "03:00")
        assert track_list.row_count == 1


def test_ui_now_playing_update():
    np_panel = NowPlaying()
    with patch.object(np_panel, "query_one") as mock_query:
        mock_display = MagicMock()
        mock_art = MagicMock()
        def side_effect(cls):
            from tuneterm.ui.now_playing import TrackInfoDisplay
            if cls == TrackInfoDisplay:
                return mock_display
            return mock_art
        mock_query.side_effect = side_effect
        np_panel.update_track("Song Title", "Artist Name", "Album Name", b"dummy")
        mock_display.update_info.assert_called_once_with("Song Title", "Artist Name", "Album Name")
        mock_art.set_art.assert_called_once_with(b"dummy")


def test_ui_playback_controls_state():
    controls = PlaybackControls()
    controls.position = 30.0
    controls.duration = 100.0
    controls.is_playing = True
    assert controls.position == 30.0

# ==============================================================================
# TIER 2: Boundary & Corner Cases (26 tests)
# ==============================================================================

def test_boundary_engine_non_existent_file():
    engine = VLCAudioEngine()
    engine.play("this_file_does_not_exist.mp3")
    assert engine.is_playing() is False


def test_boundary_engine_volume_underflow():
    engine = VLCAudioEngine()
    engine.set_volume(-50)
    assert engine.get_volume() == 0


def test_boundary_engine_volume_overflow():
    engine = VLCAudioEngine()
    engine.set_volume(250)
    assert engine.get_volume() == 100


def test_boundary_engine_already_playing():
    engine = VLCAudioEngine()
    engine.play("track1.mp3")
    engine.play("track1.mp3")
    assert engine.is_playing() is True


def test_boundary_engine_stop_uninitialized():
    engine = VLCAudioEngine()
    engine.stop()
    assert engine.is_playing() is False


def test_boundary_seek_negative():
    engine = VLCAudioEngine()
    engine.play("track1.mp3")
    engine.seek_absolute(-10.0)
    assert engine.get_position() == 0.0


def test_boundary_seek_past_duration():
    engine = VLCAudioEngine()
    engine.play("track1.mp3")
    engine.seek_absolute(500.0)
    assert engine.get_position() == 180.0


def test_boundary_seek_while_stopped():
    engine = VLCAudioEngine()
    engine.seek_absolute(10.0)
    assert engine.get_position() == 0.0


def test_boundary_seek_zero():
    engine = VLCAudioEngine()
    engine.play("track1.mp3")
    engine.seek_absolute(0.0)
    assert engine.get_position() == 0.0


def test_boundary_seek_rapid_succession():
    engine = VLCAudioEngine()
    engine.play("track1.mp3")
    for i in range(10):
        engine.seek_absolute(float(i))
    assert engine.get_position() == 9.0


def test_boundary_playlist_prev_empty():
    playlist = Playlist()
    assert playlist.previous() is None


def test_boundary_playlist_next_end_no_repeat():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.next()
    assert playlist.next() is None


def test_boundary_playlist_remove_invalid_index():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.remove(99)
    assert len(playlist.tracks) == 1


def test_boundary_playlist_shuffle_empty():
    playlist = Playlist()
    playlist.is_shuffled = True
    playlist._rebuild_shuffle()
    assert len(playlist._shuffled_indices) == 0


def test_boundary_playlist_shuffle_single():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.is_shuffled = True
    playlist._rebuild_shuffle()
    assert len(playlist._shuffled_indices) == 1


def test_boundary_playlist_concurrent_write():
    playlist = Playlist()
    def writer():
        for i in range(10):
            playlist.add(f"track_{i}.mp3")
    threads = [threading.Thread(target=writer) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(playlist.tracks) == 50


def test_boundary_stream_malformed_url():
    playlist = Playlist()
    playlist.add("invalid_url_http")
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "invalid_url_http"


def test_boundary_stream_network_timeout():
    from tuneterm.player.streaming import get_youtube_stream_info
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["cmd"], 5)):
        info = get_youtube_stream_info("https://youtube.com/watch?v=timeout")
        assert info == {}


def test_boundary_stream_no_audio():
    from tuneterm.player.streaming import get_youtube_stream_info
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "{}"
        mock_run.return_value = mock_proc
        info = get_youtube_stream_info("https://youtube.com/watch?v=no_audio")
        assert info == {}


def test_boundary_stream_missing_ytdlp():
    from tuneterm.player.streaming import get_youtube_stream_info
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        info = get_youtube_stream_info("https://youtube.com/watch?v=no_ytdlp")
        assert info == {}


def test_boundary_stream_malformed_cover_art():
    playlist = Playlist()
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        playlist.add("https://youtube.com/watch?v=123")
        assert playlist.tracks[0].cover_art_bytes is None


@pytest.mark.asyncio
async def test_boundary_ui_rapid_keys():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        for _ in range(20):
            await pilot.press("space")


@pytest.mark.asyncio
async def test_boundary_ui_directory_no_permission():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        browser = app.query_one(FileBrowser)
        with patch("pathlib.Path.iterdir", side_effect=PermissionError()):
            browser.load_directory("restricted")
            assert str(browser.path) == "restricted"


@pytest.mark.asyncio
async def test_boundary_ui_delete_empty_table():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        track_list = app.query_one(TrackList)
        track_list.action_delete_track()
        assert track_list.row_count == 0


def test_boundary_ui_invalid_music_dir():
    app = TuneTermApp(music_dir="/non_existent_dir_12345")
    assert app.music_dir == "/non_existent_dir_12345"


@pytest.mark.asyncio
async def test_boundary_ui_rapid_modal():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        await pilot.press("u")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

# ==============================================================================
# TIER 3: Cross-Feature Combinations (6 tests)
# ==============================================================================

def test_combo_shuffle_repeat_all_navigation():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.add("song3.mp3")
    playlist.toggle_shuffle()
    playlist.repeat_mode = RepeatMode.ALL
    
    first = playlist.next()
    assert first is not None
    second = playlist.next()
    assert second is not None
    third = playlist.next()
    assert third is not None
    fourth = playlist.next()
    assert fourth is not None
    
    back1 = playlist.previous()
    assert back1 is not None


@pytest.mark.asyncio
async def test_combo_seek_during_stream_load():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.add_url_and_play("https://youtube.com/watch?v=slow")
        for _ in range(50):
            if len(app.playlist.tracks) == 1:
                break
            await pilot.pause(0.1)
        assert len(app.playlist.tracks) == 1
        app.engine.seek_absolute(10.0)
        assert app.engine.get_position() == 10.0


@pytest.mark.asyncio
async def test_combo_visualizer_tab_switching():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        vis = app.query_one(Visualizer)
        assert vis.is_playing is False
        
        app.engine.play("track.mp3")
        app.update_playback_status()
        assert vis.is_playing is True
        
        app.engine.stop()
        app.update_playback_status()
        assert vis.is_playing is False


def test_combo_equalizer_preset_active_play():
    engine = VLCAudioEngine()
    eq = Equalizer(engine)
    engine.play("track.mp3")
    
    eq.apply_preset("Rock")
    assert eq.current_preset == "Rock"
    assert eq.bands == [8.0, 4.0, -4.0, -8.0, -3.0, 4.0, 8.0, 11.0, 11.0, 11.0]
    
    eq.set_band(0, 10.0)
    assert eq.current_preset == "Custom"
    assert eq.bands[0] == 10.0


@pytest.mark.asyncio
async def test_combo_add_tracks_during_search():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        search_modal = SearchModal()
        app.push_screen(search_modal)
        await pilot.pause()
        
        app.playlist.add("new_track.mp3")
        assert len(app.playlist.tracks) == 1
        
        app.pop_screen()
        await pilot.pause()


def test_combo_playlist_remove_current_playing():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.current_index = 0
    
    playlist.remove(0)
    assert playlist.current_index == -1
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "song2"

# ==============================================================================
# TIER 4: Real-World Scenarios (5 workloads)
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_setup_and_play():
    temp_music_dir = tempfile.TemporaryDirectory()
    p = Path(temp_music_dir.name)
    dummy_file = p / "track1.mp3"
    dummy_file.write_bytes(b"dummy")
    
    app = TuneTermApp(music_dir=temp_music_dir.name)
    async with app.run_test() as pilot:
        assert app.music_dir == temp_music_dir.name
        
        track_list = app.query_one(TrackList)
        app.playlist.add(str(dummy_file))
        track_list.add_row("track1", "Mock Artist", "Mock Album", "03:00")
        
        app.play_track(0)
        await pilot.pause()
        
        assert app.engine.is_playing() is True
        assert app.playlist.current_index == 0
        
    temp_music_dir.cleanup()


@pytest.mark.asyncio
async def test_scenario_stream_session():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        await pilot.press("u")
        await pilot.pause()
        modal = app.screen
        modal.query_one("#url-input").value = "https://youtube.com/watch?v=1"
        await pilot.press("enter")
        for _ in range(50):
            if len(app.playlist.tracks) == 1:
                break
            await pilot.pause(0.1)
        
        await pilot.press("u")
        await pilot.pause()
        modal = app.screen
        modal.query_one("#url-input").value = "https://youtube.com/watch?v=2"
        await pilot.press("enter")
        for _ in range(50):
            if len(app.playlist.tracks) == 2:
                break
            await pilot.pause(0.1)
        
        await pilot.press("u")
        await pilot.pause()
        modal = app.screen
        modal.query_one("#url-input").value = "https://youtube.com/watch?v=3"
        await pilot.press("enter")
        for _ in range(50):
            if len(app.playlist.tracks) == 3:
                break
            await pilot.pause(0.1)
        
        await pilot.press("s")
        await pilot.pause()
        assert app.playlist.is_shuffled is True
        
        await pilot.press("n")
        await pilot.pause()
        assert app.engine.is_playing() is True
        
        await pilot.press("n")
        await pilot.pause()
        assert app.engine.is_playing() is True


@pytest.mark.asyncio
async def test_scenario_heavy_tui_session():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.playlist.add("song1.mp3")
        app.play_track(0)
        
        from tuneterm.ui.equalizer_panel import EqualizerPanel
        eq_panel = EqualizerPanel()
        app.push_screen(eq_panel)
        await pilot.pause()
        
        select = eq_panel.query_one("#eq-preset-select")
        select.value = "Rock"
        
        await pilot.press("escape")
        await pilot.pause()
        
        await pilot.press("r")
        await pilot.pause()
        assert app.playlist.repeat_mode == RepeatMode.ALL
        
        controls = app.query_one(PlaybackControls)
        assert controls.repeat == "ALL"


@pytest.mark.asyncio
async def test_scenario_error_handling_recovery():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.playlist.add("corrupt.mp3")
        
        with patch.object(app.engine, "play", side_effect=Exception("VLC Error")):
            try:
                app.play_track(0)
            except Exception:
                pass
                
        app.playlist.add("valid.mp3")
        app.play_track(1)
        
        assert app.engine.is_playing() is True


@pytest.mark.asyncio
async def test_scenario_multiscreen_workflow():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.playlist.add("track1.mp3")
        app.play_track(0)
        
        await pilot.press("o")
        await pilot.pause()
        assert isinstance(app.screen, FirstRunScreen)
        
        app.pop_screen()
        await pilot.pause()
        
        for i in range(2, 7):
            app.playlist.add(f"track{i}.mp3")
            app.query_one(TrackList).add_row(f"track{i}", "Mock Artist", "Mock Album", "03:00")
            
        assert len(app.playlist.tracks) == 6
        
        track_list = app.query_one(TrackList)
        track_list.move_cursor(row=0, column=0)
        track_list.action_delete_track()
        
        await pilot.pause()
        
        assert len(app.playlist.tracks) == 5
        assert track_list.row_count == 5
