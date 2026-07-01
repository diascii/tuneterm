# TuneTerm Testing Infrastructure

This document outlines the testing strategy, mocking architecture, and verification protocol for the **TuneTerm** project.

---

## 1. Overview & Objectives

The primary objective of the testing suite is to provide high-fidelity, reproducible, and environment-independent testing of the TuneTerm terminal music player TUI and backend.

Due to the heavy reliance on native components (`libvlc` binaries) and physical hardware dependencies (audio output devices and loopback microphones for the visualizer), the test suite requires robust mocked interfaces. 

### Core Goals:
1. **Environment Independence**: Run tests cleanly in headless CI environments, virtual machines, or local developer setups without requiring physical audio hardware or local VLC installations.
2. **Deterministic Playback Logic**: Mock playback states (time, volume, duration) and state changes to ensure synchronous, deterministic test assertions.
3. **Thread Safety Verification**: Prevent regressions related to C-level callbacks, asynchronous operations, and database threads.
4. **Structured Coverage**: Define and enforce test coverage across 4 logical testing tiers.

---

## 2. Test Mocks Architecture

We intercept external system imports at the test entry point using `pytest` fixtures and the `sys.modules` registry. This isolates the application core from the underlying operating system audio stack.

### A. Mocking VLC (`python-vlc`)
`import vlc` is evaluated at import time in `tuneterm/player/engine.py` and `tuneterm/player/equalizer.py`. If libvlc DLLs/SOs are missing, the import crashes. 

We resolve this by registering a mocked module structure in `sys.modules['vlc']` before the codebase under test is imported.

#### Mock Attributes:
- **`vlc.EventType`**: Encapsulates `MediaPlayerEndReached`, `MediaPlayerEncounteredError`, and `MediaPlayerTimeChanged`.
- **`vlc.Instance`**: Emulates the VLC runtime environment. Exposes:
  - `media_player_new()`: Returns a stateful mock player.
  - `media_new(filepath)`: Returns a media object wrapping the filepath.
- **Stateful Player Mock**: Simulates player playback state:
  - `_playing`: Boolean tracking current playback.
  - `_volume`: Volume integer bounded between `0` and `100`.
  - `_time`: Track playback time in milliseconds.
  - `_length`: Simulated track length (default 180,000ms / 3 minutes).
  - `_callbacks`: Tracks registered event callback functions.
  - `trigger_event(event_type, event_obj)`: Diagnostic method to manually fire track-end or time-change event handlers during tests.
- **`vlc.AudioEqualizer`**: Emulates preamp and 10-band equalizer settings.

### B. Mocking Audio Input/Output (`soundcard`)
The spectrum visualizer in `tuneterm/ui/visualizer.py` captures system loopback audio using `soundcard`. We mock `soundcard` to prevent tests from failing on systems without output devices or loopback capture drivers.

#### Mock Attributes:
- **`soundcard.default_speaker()`**: Returns a dummy speaker object.
- **`soundcard.all_microphones(include_loopback=True)`**: Returns a mock microphone matching the default speaker name, with `isloopback=True`.
- **Microphone Recorder context manager**: Yields a recorder mock whose `record(numframes)` method returns a pre-configured NumPy array (e.g., shape `(1024, 2)` containing zeros or random noise), satisfying the FFT analysis loop.

---

## 3. Test Tiers Structure

To ensure thorough validation of functionality and robustness, the test suite is partitioned into four distinct tiers:

### Tier 1: Feature Coverage (Minimum 5 tests per feature)
Verifies that all core features function correctly in typical success paths.

1. **Playback Engine**:
   - `test_engine_play`: Playback transition and loading media.
   - `test_engine_pause`: Toggling and verifying pause states.
   - `test_engine_stop`: Media player stopping and time reset.
   - `test_engine_volume_set`: Setting volume updates the volume tracker.
   - `test_engine_callbacks`: Attaching and firing event handlers.
2. **Seeking**:
   - `test_seek_absolute`: Seeking to specific timestamps.
   - `test_seek_relative_forward`: Seeking forward.
   - `test_seek_relative_backward`: Seeking backward.
   - `test_seek_length_retrieval`: Correct duration mapping.
   - `test_seek_position_retrieval`: Correct current position mapping.
3. **Playlist Management**:
   - `test_playlist_add`: Adding local filepaths.
   - `test_playlist_remove`: Deleting indices and updating current index pointers.
   - `test_playlist_clear`: Purging playlist queue.
   - `test_playlist_navigation`: Moving sequentially using `next()` and `previous()`.
   - `test_playlist_shuffle`: Enabling shuffle mode generates random index queues.
4. **URL Streaming**:
   - `test_stream_url_extraction`: yt-dlp parsing mock output.
   - `test_stream_add_url_to_playlist`: Loading and parsing streaming tracks.
   - `test_stream_play_url`: Feeding extracted audio URLs to the media player.
   - `test_stream_thumbnail_download`: Mocking thumbnail fetches for cover art.
   - `test_stream_fallback_parsing`: yt-dlp parsing fallback.
5. **UI Widgets & Views**:
   - `test_ui_file_browser_load`: File tree rendering.
   - `test_ui_track_list_render`: List table populated with tracks.
   - `test_ui_now_playing_update`: Art and metadata populated upon playback.
   - `test_ui_playback_controls_state`: Volume and progress bars updating.
   - `test_ui_help_modal`: Shortcuts window rendering.

### Tier 2: Boundary & Corner Cases (Minimum 5 tests per feature)
Verifies the resilience of the application under unexpected, invalid, or boundary inputs.

1. **Playback Engine**:
   - Playback of non-existent/corrupted filepaths.
   - Volume parameter set below `0` (asserts clamped to `0`).
   - Volume parameter set above `100` (asserts clamped to `100`).
   - Playing when player is already playing.
   - Stopping an uninitialized/empty playback engine.
2. **Seeking**:
   - Seeking to a negative position (asserts clamped to `0`).
   - Seeking past track duration (asserts clamped to track length).
   - Seeking while playback is stopped.
   - Zero-second seek operations.
   - Multi-step seek operations in rapid succession.
3. **Playlist Management**:
   - Backwards navigation (`previous()`) on a new or empty playlist.
   - Forward navigation (`next()`) at the end of playlist with repeat off.
   - Deleting non-existent indices.
   - Shuffling an empty playlist or a single-track playlist.
   - Concurrently writing to playlist from worker thread while UI reads.
4. **URL Streaming**:
   - Inputting malformed/empty URLs.
   - Mocking network timeouts and verifying UI resilience.
   - Extracting tracks where YouTube stream has no audio source.
   - yt-dlp missing command-line executable checks.
   - Downloading malformed cover art image data.
5. **UI & Keyboard Inputs**:
   - Rapid keyboard inputs (hammering keys).
   - Reading directories without permission (verifies screen warning/no crash).
   - Removing tracks when the table is empty.
   - Launching app with invalid music directory config.
   - Rapid modal switching.

### Tier 3: Cross-Feature Combinations
Tests the intersection of multiple features interacting concurrently.

- **Shuffle + Repeat All + Navigation**: Ensuring index history maintains sequence integrity.
- **Seeking during Stream Extraction**: Performing seek operations on slow-loading URL buffers.
- **Active Visualizer during Tab Switching**: Verifying the spectrum analyzer thread sleeps/resumes properly without UI lockups.
- **Equalizer Preset changes during Active Playback**: Verifying EQ state pushes to the active VLC player instance.
- **Adding tracks while searching**: Modifying playlist structures during active library queries.

### Tier 4: Real-World Application Scenarios
End-to-End user session workflows simulated programmatically.

- **Scenario 1: Setup & Play**: Welcome Screen -> set directory -> load tracks -> select first song -> verify playback controls update.
- **Scenario 2: Stream Session**: Add 3 streaming URLs -> shuffle -> skip through URLs -> verify correct yt-dlp lookup and no deadlock.
- **Scenario 3: Heavy TUI Session**: Play song -> open Equalizer modal -> adjust 3 sliders -> close modal -> toggle shuffle -> pause -> check progress bar.
- **Scenario 4: Error Handling Recovery**: Attempt invalid file playback -> click off popup -> select valid stream -> verify visualizer and player resume normally.
- **Scenario 5: Multi-screen workflow**: Play local track -> open folder modal -> navigate directory -> add 5 tracks -> delete 2 tracks -> verify table synchronization.

---

## 4. Textual UI Testing Strategy

We test the Textual frontend using Textual's built-in testing client, `App.run_test`. This allows headless, event-driven interactions.

```python
async def test_playback_toggle_key():
    from tuneterm.ui.app import TuneTermApp
    
    app = TuneTermApp()
    async with app.run_test() as pilot:
        # Simulate pressing spacebar to toggle play/pause
        await pilot.press("space")
        
        # Query controls component and verify states
        controls = app.query_one("#playback-controls")
        assert controls.is_playing is True
        
        # Press spacebar again
        await pilot.press("space")
        assert controls.is_playing is False
```

---

## 5. Running the Tests

### Command Guide:

- **Run all tests**:
  ```bash
  pytest tests/
  ```
- **Verbose execution**:
  ```bash
  pytest tests/ -vv -s
  ```
- **Generate Coverage Report**:
  ```bash
  pytest tests/ --cov=tuneterm --cov-report=term-missing
  ```

---

## 6. Sign-off & Verification

Once the tests are written and fully passing, a `TEST_READY.md` sign-off file is generated at the project root with the following template:

```markdown
# Test Suite Readiness Verification

- All tests (Tiers 1-4) implemented: [Yes/No]
- VLC Mock verified: [Yes/No]
- Soundcard Mock verified: [Yes/No]
- Pytest run verdict: [PASSED]
- Code Coverage achieved: [XX]%
```
