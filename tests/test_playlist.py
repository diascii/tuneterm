import pytest
import threading
import time
from tuneterm.player.playlist import Playlist, RepeatMode

# ==============================================================================
# Tier 1: Playlist Management Feature Coverage
# ==============================================================================

def test_playlist_add():
    playlist = Playlist()
    track1 = playlist.add("song1.mp3")
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "song1"
    assert track1.title == "song1"

def test_playlist_remove():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.add("song3.mp3")
    
    # Remove middle song
    playlist.remove(1)
    assert len(playlist.tracks) == 2
    assert playlist.tracks[0].title == "song1"
    assert playlist.tracks[1].title == "song3"

def test_playlist_clear():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.clear()
    assert len(playlist.tracks) == 0
    assert playlist.current_index == -1

def test_playlist_navigation():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    playlist.add("song3.mp3")
    
    # Starting state
    assert playlist.current_index == -1
    
    # Next transitions
    t1 = playlist.next()
    assert t1.title == "song1"
    assert playlist.current_index == 0
    
    t2 = playlist.next()
    assert t2.title == "song2"
    assert playlist.current_index == 1
    
    t3 = playlist.next()
    assert t3.title == "song3"
    assert playlist.current_index == 2
    
    # Previous transitions
    t2_back = playlist.previous()
    assert t2_back.title == "song2"
    assert playlist.current_index == 1
    
    t1_back = playlist.previous()
    assert t1_back.title == "song1"
    assert playlist.current_index == 0

def test_playlist_shuffle():
    playlist = Playlist()
    for i in range(10):
        playlist.add(f"song{i}.mp3")
        
    assert playlist.is_shuffled is False
    playlist.toggle_shuffle()
    assert playlist.is_shuffled is True
    
    # The shuffled indices should be a permutation of 0-9
    assert sorted(playlist._shuffled_indices) == list(range(10))


# ==============================================================================
# Tier 2: Playlist Management Boundary & Corner Cases
# ==============================================================================

def test_playlist_previous_empty():
    playlist = Playlist()
    assert playlist.previous() is None

def test_playlist_next_end_no_repeat():
    playlist = Playlist()
    playlist.add("song1.mp3")
    playlist.add("song2.mp3")
    
    # Go to end
    playlist.next()
    playlist.next()
    
    # Assert next returns None since repeat is off
    assert playlist.repeat_mode == RepeatMode.OFF
    assert playlist.next() is None

def test_playlist_remove_non_existent_indices():
    playlist = Playlist()
    playlist.add("song1.mp3")
    
    # Attempting to remove out of bounds should do nothing and not crash
    playlist.remove(-1)
    playlist.remove(5)
    assert len(playlist.tracks) == 1
    assert playlist.tracks[0].title == "song1"

def test_playlist_shuffle_empty_single():
    playlist = Playlist()
    # Shuffle empty
    playlist.toggle_shuffle()
    assert playlist.is_shuffled is True
    assert len(playlist._shuffled_indices) == 0
    
    # Shuffle single
    playlist.toggle_shuffle() # turn off
    playlist.add("single.mp3")
    playlist.toggle_shuffle() # turn on
    assert len(playlist._shuffled_indices) == 1
    assert playlist._shuffled_indices == [0]

def test_playlist_concurrent_write_read():
    playlist = Playlist()
    stop_event = threading.Event()
    
    def writer():
        for i in range(100):
            playlist.add(f"concurrent_track_{i}.mp3")
            time.sleep(0.001)
            
    def reader():
        while not stop_event.is_set():
            _ = playlist.tracks
            _ = playlist.current()
            time.sleep(0.002)
            
    write_thread = threading.Thread(target=writer)
    read_thread = threading.Thread(target=reader)
    
    read_thread.start()
    write_thread.start()
    
    write_thread.join()
    stop_event.set()
    read_thread.join()
    
    assert len(playlist.tracks) == 100
