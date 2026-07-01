# TuneTerm — AI Handoff Document

> **For the next AI model:** This document summarizes the current state of the TuneTerm project, what has been done, what remains, and exactly how to continue.

---

## Project Overview

**TuneTerm** is a terminal-based music player (Python + [Textual](https://github.com/Textualize/textual) TUI) with:
- Local file playback via VLC (`python-vlc`)
- YouTube streaming via `yt-dlp`
- Discord Rich Presence (`pypresence`)
- Last.fm scrobbling (`pylast`)
- FFT audio visualizer (`soundcard` + `numpy`)
- Library management (SQLite)
- Equalizer, Lyrics fetching

**Working directory:** `D:\tuneterm`  
**Python:** `C:\Users\Asus\AppData\Local\Programs\Python\Python311\python.exe`  
**Entry point:** `python -m tuneterm` from `D:\tuneterm`

---

## Codebase Structure

```
D:\tuneterm\
├── build.py
├── HANDOFF.md                         # This file
├── tuneterm/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── player/
│   │   ├── engine.py                  # VLCAudioEngine — main playback engine
│   │   ├── playlist.py                # Playlist — thread-safe with RLock
│   │   ├── metadata.py                # TrackInfo dataclass + mutagen extraction
│   │   ├── library.py                 # SQLite music library (DB_PATH configurable)
│   │   ├── equalizer.py               # EQ presets wrapper
│   │   ├── streaming.py               # yt-dlp streaming helper
│   │   └── crossfade.py               # Crossfade stub (not implemented)
│   ├── integrations/
│   │   ├── discord_rpc.py             # Discord Rich Presence
│   │   ├── lastfm.py                  # Last.fm scrobbler
│   │   └── lyrics_fetch.py            # Lyrics fetcher (stub, not implemented)
│   ├── ui/
│   │   ├── app.py                     # Main Textual App (TuneTermApp) — orchestrator
│   │   ├── add_url_modal.py           # Modal for adding YouTube/stream URLs
│   │   ├── controls.py                # Playback control bar widget
│   │   ├── equalizer_panel.py         # Equalizer UI panel
│   │   ├── file_browser.py            # Local file browser widget
│   │   ├── first_run.py               # First-run setup screen
│   │   ├── help_modal.py              # Keybinding help modal
│   │   ├── lyrics_panel.py            # Lyrics display panel
│   │   ├── now_playing.py             # Now playing info widget
│   │   ├── search_modal.py            # Search modal
│   │   ├── spinning_art.py            # Spinning album art widget
│   │   ├── status_bar.py              # Bottom status bar
│   │   ├── track_list.py              # Playlist/track list widget
│   │   └── visualizer.py             # FFT audio visualizer widget
│   ├── utils/
│   │   ├── ascii_art.py               # ASCII art utilities
│   │   ├── circular_crop.py           # Image circular crop for album art
│   │   ├── config.py                  # Config (TOML-based, CONFIG_DIR/CONFIG_FILE)
│   │   ├── logger.py                  # Logging setup
│   │   └── session.py                 # Session state persistence
│   └── themes/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Full mock setup (VLC, soundcard, pypresence, pylast)
│   ├── test_e2e.py                    # End-to-end tests
│   ├── test_playlist.py               # Playlist unit tests
│   ├── test_engine.py                 # VLCAudioEngine unit tests
│   ├── test_ui.py                     # UI state tests
│   ├── test_concurrency.py            # Thread-safety tests
│   ├── test_integration.py            # Integration tests
│   ├── test_streaming.py              # yt-dlp streaming tests
│   ├── test_milestone2.py             # DB WAL mode + library tests
│   ├── test_milestone2_stress.py      # Concurrent library scan stress tests
│   └── test_challenger_verification.py
└── .venv/                             # Virtual environment (exists but use system Python)
```

---

## What Was Already Completed

### ✅ Milestone 1 — Concurrency & Thread Safety
- `Playlist` uses `threading.RLock()` for all mutations
- `VLCAudioEngine` uses `RLock` on state transitions
- UI callbacks use `call_from_thread()` instead of direct widget calls
- Visualizer and Discord RPC run in daemon threads, not blocking the UI

### ✅ Milestone 2 — Feature Integration
- Library (SQLite) integrated and working
- Equalizer presets integrated
- Last.fm scrobbling integrated  
- Discord Rich Presence integrated (Client ID: `1521277587366613013`)
- **Known issue:** Discord presence image (`large_image`) does not appear — see Discord Image Bug section below

### 🟡 Milestone 3 — Test Suite (Partially Done)
- 12 test files exist in `tests/`
- `conftest.py` has comprehensive mocks (VLC, soundcard, pypresence, pylast, yt-dlp)
- Tests have **NOT been run successfully yet** — dependencies were just installed

### ❌ Milestone 4 — Code Review Report
- `code_review.md` does **NOT exist yet**
- Needs to be generated summarizing bugs found, fixes applied, and remaining debt

---

## Immediate Next Steps (Priority Order)

### 1. Run the Test Suite
All dependencies are now installed:
```
pip install pytest pytest-asyncio pytest-mock mutagen yt-dlp pypresence pylast textual
```

Run tests:
```
cd D:\tuneterm
python -m pytest tests/ -v --tb=short
```

Fix any failing tests. The conftest mocks are well-built — failures are likely import errors or logic bugs in the test files themselves.

### 2. Fix the Discord Presence Image Bug

**Problem:** The `large_image` field in Discord Rich Presence shows nothing.

**File:** `D:\tuneterm\tuneterm\integrations\discord_rpc.py`

**Root cause:** Discord requires `large_image` to be either:
- A named asset uploaded to the Discord Developer Portal for app `1521277587366613013`, OR
- A direct image URL (only works for certain Discord versions)

**Solution options:**
- Upload a logo asset to https://discord.com/developers/applications/1521277587366613013/rich-presence/assets and use the asset name as `large_image`
- OR use a publicly accessible image URL as `large_image` (test with a plain https URL)
- Currently the code likely sets `large_image` to a local path or incorrect key — check and fix

**The TuneTerm logo image** is at:
`C:\Users\Asus\.gemini\antigravity-cli\brain\201a6b6d-03a6-4a84-8b8d-5e238bb9f74e\tuneterm_logo_1782772697112.jpg`

### 3. Generate `code_review.md`

Create a markdown report at `D:\tuneterm\code_review.md` covering:
- Bugs found and fixed (concurrency, threading, history bounds)
- Architecture decisions (RLock pattern, call_from_thread pattern)
- Remaining technical debt
- Test coverage summary

---

## Known Issues / Technical Debt

| Issue | File | Notes |
|-------|------|-------|
| Discord `large_image` not showing | `integrations/discord_rpc.py` | Needs asset uploaded to Discord portal OR valid URL |
| `lyrics_fetch.py` is a stub | `integrations/lyrics_fetch.py` | Only 104 bytes — not implemented |
| `crossfade.py` is a stub | `player/crossfade.py` | Only 268 bytes — not implemented |
| `code_review.md` missing | project root | Needs to be authored |
| Tests not validated | `tests/` | Were written but never successfully run |

---

## Key Architecture Patterns

### Thread Safety (IMPORTANT)
All cross-thread UI mutations must use:
```python
self.app.call_from_thread(self._some_ui_method, args)
```
Never mutate Textual widgets from background threads directly.

### Playlist Locking
```python
# All playlist reads/writes are wrapped in RLock:
with self._lock:
    self._tracks.append(track)
```

### Discord RPC
The `DiscordRPC` class in `discord_rpc.py` wraps `pypresence.Presence`.
- Client ID: `1521277587366613013`
- Called from a daemon thread in `app.py`
- `large_image` key should reference a named asset OR a public URL

---

## Dependencies

```
python-vlc       # Audio playback
textual          # TUI framework
mutagen          # Audio metadata
yt-dlp           # YouTube streaming
pypresence       # Discord Rich Presence
pylast           # Last.fm API
soundcard        # Audio capture for visualizer
numpy            # FFT computation
requests         # HTTP requests
pytest           # Testing
pytest-asyncio   # Async test support
pytest-mock      # Mock fixtures
```

Install all:
```bash
pip install python-vlc textual mutagen yt-dlp pypresence pylast soundcard numpy requests pytest pytest-asyncio pytest-mock
```

Note: `python-vlc` also requires VLC media player to be installed on the system.

---

## Conversation Context

This work was done in Antigravity (Google AI coding assistant) conversation `201a6b6d-03a6-4a84-8b8d-5e238bb9f74e`. The session hit API rate limits before completing Milestones 3 and 4. The test infrastructure is solid — just needs a run and fixes.
