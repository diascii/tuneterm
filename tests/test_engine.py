import pytest
from unittest.mock import MagicMock
import vlc
from tuneterm.player.engine import VLCAudioEngine

# ==============================================================================
# Tier 1: Playback Engine Feature Coverage
# ==============================================================================

def test_engine_play():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    assert engine.is_playing() is True
    assert engine.player.get_media().get_mrl() == "test_track.mp3"

def test_engine_pause():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.pause()
    assert engine.is_playing() is False
    engine.resume()
    assert engine.is_playing() is True

def test_engine_stop():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.stop()
    assert engine.is_playing() is False
    assert engine.get_position() == 0.0

def test_engine_volume_set():
    engine = VLCAudioEngine()
    engine.set_volume(80)
    assert engine.get_volume() == 80
    engine.set_volume(20)
    assert engine.get_volume() == 20

def test_engine_playback_state_transitions():
    """Engine correctly tracks playing state without callbacks (polling-based)."""
    engine = VLCAudioEngine()
    
    # Initially not playing
    assert engine.is_playing() is False
    assert engine.get_position() == 0.0
    
    # After play, is_playing returns True
    engine.play("test_track.mp3")
    assert engine.is_playing() is True
    
    # After stop, is_playing returns False, position resets
    engine.stop()
    assert engine.is_playing() is False
    assert engine.get_position() == 0.0


# ==============================================================================
# Tier 1: Seeking Feature Coverage
# ==============================================================================

def test_seek_absolute():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.seek_absolute(30.0)
    assert engine.get_position() == 30.0

def test_seek_relative_forward():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.seek_absolute(10.0)
    engine.seek_relative(15.0)
    assert engine.get_position() == 25.0

def test_seek_relative_backward():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.seek_absolute(40.0)
    engine.seek_relative(-15.0)
    assert engine.get_position() == 25.0

def test_seek_length_retrieval():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.player._length = 240000  # 4 minutes
    assert engine.get_duration() == 240.0

def test_seek_position_retrieval():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.player._time = 90000  # 90 seconds
    assert engine.get_position() == 90.0


# ==============================================================================
# Tier 2: Boundary & Corner Cases (Playback Engine & Seeking)
# ==============================================================================

def test_engine_non_existent_corrupted_filepaths():
    engine = VLCAudioEngine()
    # Playing a non-existent file results in stopped state (no callback needed)
    engine.play("does_not_exist.mp3")
    assert engine.is_playing() is False

def test_engine_volume_underflow_clamped():
    engine = VLCAudioEngine()
    engine.set_volume(-10)
    assert engine.get_volume() == 0

def test_engine_volume_overflow_clamped():
    engine = VLCAudioEngine()
    engine.set_volume(150)
    assert engine.get_volume() == 100

def test_engine_play_when_already_playing():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    assert engine.is_playing() is True
    engine.play("test_track.mp3")
    assert engine.is_playing() is True

def test_engine_stop_uninitialized_empty():
    engine = VLCAudioEngine()
    # Stopping an uninitialized/empty engine should be safe and not raise exceptions
    engine.stop()
    assert engine.is_playing() is False

def test_seek_negative_clamped():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.seek_absolute(-5.0)
    assert engine.get_position() == 0.0

def test_seek_past_track_length_clamped():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.player._length = 120000  # 2 minutes (120 seconds)
    engine.seek_absolute(150.0)
    assert engine.get_position() == 120.0

def test_seek_while_stopped():
    engine = VLCAudioEngine()
    # If the player is stopped, get_time() returns -1, which engine maps to 0.0
    engine.stop()
    engine.seek_absolute(30.0)
    assert engine.get_position() == 0.0

def test_seek_zero_seconds():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    engine.seek_absolute(0.0)
    assert engine.get_position() == 0.0

def test_seek_multistep_rapid():
    engine = VLCAudioEngine()
    engine.play("test_track.mp3")
    for sec in [5.0, 10.0, 15.0, 20.0]:
        engine.seek_absolute(sec)
    assert engine.get_position() == 20.0
