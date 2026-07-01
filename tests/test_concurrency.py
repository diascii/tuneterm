import pytest
import threading
import time
from unittest.mock import MagicMock
from tuneterm.player.playlist import Playlist
from tuneterm.ui.visualizer import Visualizer
from tuneterm.integrations.discord_rpc import DiscordRPC
from tuneterm.ui.app import TuneTermApp

def test_playlist_tracks_copy():
    """
    If this test fails, playlist.tracks property does not return a copied list,
    allowing external callers to mutate the internal state directly.
    """
    playlist = Playlist()
    playlist.add("dummy_path")
    
    tracks_list_1 = playlist.tracks
    tracks_list_2 = playlist.tracks
    
    assert tracks_list_1 == tracks_list_2
    assert tracks_list_1 is not tracks_list_2  # Must be a copy
    
    # Mutating copy should not affect internal list
    tracks_list_1.append("extra")
    assert len(playlist.tracks) == 1

def test_playlist_concurrent_access():
    """
    If this test fails, Playlist does not handle concurrent read/write state access
    safely, resulting in data races, ValueError, or IndexError.
    """
    playlist = Playlist()
    
    def writer_thread():
        for i in range(100):
            playlist.add(f"track_{i}.mp3")
            time.sleep(0.001)
            
    def reader_thread():
        for _ in range(100):
            _ = playlist.tracks
            _ = playlist.current()
            time.sleep(0.001)
            
    t1 = threading.Thread(target=writer_thread)
    t2 = threading.Thread(target=reader_thread)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    assert len(playlist.tracks) == 100

@pytest.mark.asyncio
async def test_visualizer_unmount_stops_thread():
    """
    If this test fails, the Visualizer widget does not stop or join the audio worker
    thread on unmount, causing CPU/resource leaks.
    """
    app = TuneTermApp(music_dir=".")
    async with app.run_test() as pilot:
        vis = app.query_one(Visualizer)
        assert vis.running is True
        assert vis.audio_thread.is_alive() is True
        
        vis.on_unmount()
        assert vis.running is False
        
        # Give thread a small moment to exit and join
        vis.audio_thread.join(timeout=1.0)
        assert vis.audio_thread.is_alive() is False

def test_discord_rpc_large_image():
    """
    If this test fails, DiscordRPC.update does not support dynamically passing a 
    large_image argument or fallback to logo, leading to incorrect integration states.
    """
    rpc = DiscordRPC()
    rpc.rpc = MagicMock()
    rpc.connected = True
    
    # Test update without large_image (no longer defaults to "logo" — uses public URL in app.py)
    rpc.update("details", "state")
    rpc.rpc.update.assert_called_once()
    kwargs = rpc.rpc.update.call_args[1]
    # large_image should NOT be in kwargs when not provided (discord_rpc no longer hardcodes "logo")
    assert "large_image" not in kwargs
    
    # Test update with custom large_image
    rpc.rpc.update.reset_mock()
    rpc.update("details", "state", large_image="http://example.com/art.jpg")
    rpc.rpc.update.assert_called_once()
    kwargs = rpc.rpc.update.call_args[1]
    assert kwargs["large_image"] == "http://example.com/art.jpg"


