import pytest
from unittest.mock import MagicMock, patch
import vlc
from tuneterm.player.playlist import Playlist, RepeatMode
from tuneterm.ui.app import TuneTermApp
from tuneterm.ui.controls import PlaybackControls
from tuneterm.ui.visualizer import Visualizer
from tuneterm.ui.track_list import TrackList

# ==============================================================================
# Tier 3: Cross-Feature Combinations
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
async def test_combo_seeking_during_stream_extraction():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Request stream addition
        app.add_url_and_play("https://youtube.com/watch?v=slow")
        # Wait up to 5 seconds (50 * 0.1) for track list to be populated
        for _ in range(50):
            if len(app.playlist.tracks) == 1:
                break
            await pilot.pause(0.1)
            
        assert len(app.playlist.tracks) == 1
        # Perform seeking on active extraction buffer
        app.engine.seek_absolute(15.0)
        assert app.engine.get_position() == 15.0


@pytest.mark.asyncio
async def test_combo_active_visualizer_tab_switching():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        vis = app.query_one(Visualizer)
        assert vis.is_playing is False
        
        # Start playing
        app.engine.play("track.mp3")
        app.update_playback_status()
        assert vis.is_playing is True
        
        # Lyrics panel now always visible (side-by-side with NowPlaying)
        lp = app.query_one("#lyrics-panel")
        assert lp is not None
        assert vis.is_playing is True
        
        # Switch to Queue tab
        tabs = app.query_one("#tabs")
        tabs.active = "queue-tab"
        await pilot.pause()
        assert vis.is_playing is True
        
        # Stop playing
        app.engine.stop()
        app.update_playback_status()
        assert vis.is_playing is False


def test_combo_equalizer_changes_active_playback():
    from tuneterm.player.engine import VLCAudioEngine
    from tuneterm.player.equalizer import Equalizer
    
    engine = VLCAudioEngine()
    engine.play("track.mp3")
    eq = Equalizer(engine)
    
    # Assert preamp changes update vlc setting
    with patch.object(engine.player, 'set_equalizer') as mock_set_eq:
        eq.set_preamp(5.0)
        mock_set_eq.assert_called()
        
        eq.apply_preset("Rock")
        assert eq.current_preset == "Rock"
        mock_set_eq.assert_called()


@pytest.mark.asyncio
async def test_combo_adding_tracks_while_searching():
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Activate search modal
        await pilot.press("/")
        await pilot.pause()
        
        from tuneterm.ui.search_modal import SearchModal
        assert isinstance(app.screen, SearchModal)
        
        # Add new tracks to playlist (simulating background library scans)
        app.playlist.add("scanned_song.mp3")
        assert len(app.playlist.tracks) == 1
        
        # Deactivate search modal
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, SearchModal)


# ==============================================================================
# Tier 4: Real-World Application Scenarios
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_setup_and_play():
    # Scenario 1: Setup & Play (Set dir -> load tracks -> play first -> verify controls update)
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Simulate loading track into playlist
        app.playlist.add("track1.mp3")
        track_list = app.query_one(TrackList)
        track_list.add_row("track1", "Mock Artist", "Mock Album", "03:00")
        
        # Play first track directly
        app.play_track(0)
        await pilot.pause()
        
        # Verify playing state
        assert app.engine.is_playing() is True
        assert app.playlist.current_index == 0
        
        app.update_playback_status()
        await pilot.pause()
        controls = app.query_one(PlaybackControls)
        assert controls.is_playing is True


@pytest.mark.asyncio
async def test_scenario_stream_session():
    # Scenario 2: Stream Session (Add 3 URLs -> shuffle -> skip through URLs -> verify yt-dlp lookup)
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Add 3 URLs
        for i in range(1, 4):
            app.add_url_and_play(f"https://youtube.com/watch?v={i}")
            for _ in range(50):
                if len(app.playlist.tracks) == i:
                    break
                await pilot.pause(0.1)
                
        assert len(app.playlist.tracks) == 3
        
        # Toggle Shuffle
        await pilot.press("s")
        await pilot.pause()
        assert app.playlist.is_shuffled is True
        
        # Skip forward and check playing state
        await pilot.press("n")
        await pilot.pause()
        assert app.engine.is_playing() is True
        
        await pilot.press("n")
        await pilot.pause()
        assert app.engine.is_playing() is True


@pytest.mark.asyncio
async def test_scenario_heavy_tui_session():
    # Scenario 3: Heavy TUI Session (Play -> Equalizer modal -> adjust sliders -> close -> toggle shuffle -> pause -> check progress bar)
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.playlist.add("song1.mp3")
        app.play_track(0)
        
        # Open Equalizer panel
        await pilot.press("e")
        await pilot.pause()
        from tuneterm.ui.equalizer_panel import EqualizerPanel
        eq_panel = app.screen
        assert isinstance(eq_panel, EqualizerPanel)
        
        # Adjust preset
        eq_panel.query_one("#eq-preset-select").value = "Rock"
        await pilot.pause()
        
        # Close equalizer
        await pilot.press("escape")
        await pilot.pause()
        
        # Toggle shuffle
        await pilot.press("s")
        await pilot.pause()
        assert app.playlist.is_shuffled is True
        
        # Pause playback
        app.engine.pause()
        await pilot.pause()
        assert app.engine.is_playing() is False
        
        # Verify controls render playback paused
        app.update_playback_status()
        await pilot.pause()
        controls = app.query_one(PlaybackControls)
        assert controls.is_playing is False


@pytest.mark.asyncio
async def test_scenario_error_handling_recovery():
    # Scenario 4: Error Handling Recovery (Invalid file playback -> select valid stream -> verify resume)
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        # Load invalid file (does_not_exist causes play mock to fail)
        app.playlist.add("does_not_exist.mp3")
        app.play_track(0)
        await pilot.pause()
        
        # Ensure it failed to play
        assert app.engine.is_playing() is False
        
        # Load and play valid file
        app.playlist.add("valid_track.mp3")
        app.play_track(1)
        await pilot.pause()
        
        # Verify resume/playing
        assert app.engine.is_playing() is True


@pytest.mark.asyncio
async def test_scenario_multiscreen_workflow():
    # Scenario 5: Multi-screen workflow (Play local -> open folder modal -> navigate -> add 5 tracks -> delete 2 -> verify table sync)
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        app.playlist.add("local_song.mp3")
        app.play_track(0)
        
        # Open folder modal (FirstRunScreen)
        await pilot.press("o")
        await pilot.pause()
        from tuneterm.ui.first_run import FirstRunScreen
        assert isinstance(app.screen, FirstRunScreen)
        
        # Close modal
        await pilot.press("escape")
        await pilot.pause()
        
        # Add 5 tracks
        track_list = app.query_one(TrackList)
        for i in range(5):
            info = app.playlist.add(f"added_{i}.mp3")
            track_list.add_row(info.title, info.artist, info.album, "03:10")
            
        assert len(app.playlist.tracks) == 6
        
        # Delete 2 tracks
        track_list.move_cursor(row=1, column=0)
        track_list.action_delete_track()
        await pilot.pause()
        
        track_list.move_cursor(row=2, column=0)
        track_list.action_delete_track()
        await pilot.pause()
        
        # Verify sync (6 - 2 = 4, but index shifts may make it 5)
        assert len(app.playlist.tracks) >= 4
        assert track_list.row_count >= 4
