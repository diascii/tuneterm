import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from tuneterm.ui.app import TuneTermApp
from tuneterm.ui.file_browser import FileBrowser
from tuneterm.ui.track_list import TrackList
from tuneterm.ui.now_playing import NowPlaying
from tuneterm.ui.controls import PlaybackControls
from tuneterm.ui.help_modal import HelpModal

# ==============================================================================
# Tier 1: UI Widgets & Views Feature Coverage
# ==============================================================================

@pytest.mark.asyncio
async def test_ui_file_browser_load():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        browser = app.query_one(FileBrowser)
        browser.load_directory(".")
        assert str(browser.path) == "."

@pytest.mark.asyncio
async def test_ui_track_list_render():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        track_list = app.query_one(TrackList)
        track_list.add_row("Title", "Artist", "Album", "03:15")
        assert track_list.row_count == 1

def test_ui_now_playing_update():
    np = NowPlaying()
    with patch.object(np, "query_one") as mock_query:
        mock_display = MagicMock()
        mock_art = MagicMock()
        def side_effect(cls):
            from tuneterm.ui.now_playing import TrackInfoDisplay
            from tuneterm.ui.spinning_art import SpinningArt
            if "TrackInfoDisplay" in str(cls) or cls == TrackInfoDisplay:
                return mock_display
            return mock_art
        mock_query.side_effect = side_effect
        from tuneterm.player.metadata import TrackInfo
        dummy = TrackInfo(
            filepath="", title="Song Title", artist="Artist Name", album="Album Name",
            year="", genre="", duration=0.0, bitrate=0, sample_rate=0, format=""
        )
        np.update_track(dummy, b"art_bytes")
        mock_display.update_info.assert_called_once_with(dummy)
        mock_art.set_art.assert_called_once_with(b"art_bytes")

def test_ui_playback_controls_state():
    controls = PlaybackControls()
    controls.position = 15.0
    controls.duration = 60.0
    controls.is_playing = True
    controls.shuffle = True
    controls.repeat = "ALL"
    assert controls.position == 15.0
    assert controls.duration == 60.0
    assert controls.is_playing is True
    assert controls.shuffle is True
    assert controls.repeat == "ALL"

@pytest.mark.asyncio
async def test_ui_help_modal():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        await pilot.press("?")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)


# ==============================================================================
# Tier 2: UI & Keyboard Inputs Boundary & Corner Cases
# ==============================================================================

@pytest.mark.asyncio
async def test_ui_rapid_keyboard_inputs():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Rapidly hammer control and navigation keys
        for key in ["space", "n", "p", "right", "left", "s", "r", "space"]:
            await pilot.press(key)

@pytest.mark.asyncio
async def test_ui_directory_read_no_permission():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        browser = app.query_one(FileBrowser)
        with patch("pathlib.Path.iterdir", side_effect=PermissionError("Permission Denied")):
            # Verifies FileBrowser handles PermissionError gracefully
            browser.load_directory("restricted")
            assert str(browser.path) == "restricted"

@pytest.mark.asyncio
async def test_ui_remove_track_empty_table():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        track_list = app.query_one(TrackList)
        # Removing tracks when table is empty should not raise errors
        track_list.action_delete_track()
        assert track_list.row_count == 0

def test_ui_launch_invalid_music_dir():
    # Attempt to launch the application with a non-existent or invalid directory path
    app = TuneTermApp(music_dir="/non_existent_directory_9999")
    assert app.music_dir == "/non_existent_directory_9999"

@pytest.mark.asyncio
async def test_ui_rapid_modal_switching():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Hammer opening/dismissing modals rapidly
        await pilot.press("?") # Help Modal
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        
        await pilot.press("e") # Equalizer Panel
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        
        await pilot.press("u") # Add URL Modal
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
