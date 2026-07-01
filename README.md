# 🎵 TuneTerm

**A professional-grade terminal music player** — Python + Textual TUI with VLC playback, YouTube streaming, synced lyrics, FFT visualizer, crossfade, Discord RPC & Last.fm scrobbling.

![PyPI - Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

### 🎮 Playback
- **Local files** — MP3, FLAC, WAV, OGG, M4A, etc. via VLC
- **YouTube streaming** — paste any YouTube URL, plays via `yt-dlp`
- **Crossfade** — smooth 2s fade-out/fade-in between tracks
- **10-band Equalizer** — presets (Rock, Pop, Jazz, Classical, etc.) + custom
- **Queue management** — reorder tracks with `Ctrl+↑/↓`, remove with `Delete`

### 🎨 Interface
- **Terminal UI** — built with [Textual](https://github.com/Textualize/textual)
- **21 built-in themes** — press `t` to cycle (Nord, Dracula, Tokyo Night, Catppuccin, Solarized, Rose Pine, etc.)
- **FFT Audio Visualizer** — real-time bars with AGC, log-spaced bands, fast-attack/slow-decay envelope
- **Spinning album art** — ASCII art rotation while playing
- **Synced lyrics** — fetches from LRCLIB + Lyrics.ovh fallback, auto-highlights current line
- **Marquee title** — terminal tab title scrolls when too long
- **Modals centered** — all dialogs (help, search, add URL, equalizer) centered on screen

### 🔌 Integrations
- **Discord Rich Presence** — shows currently playing track
- **Last.fm scrobbling** — auto-scrobble when tracks finish
- **Music library** — SQLite-backed (WAL mode), searchable via `/`

### 🛡️ Reliability
- **Anti-freeze** — polling-based track end detection (no VLC callback deadlocks)
- **Watchdog** — heartbeat every 30s, logs freeze detection
- **Rotating logger** — 5MB auto-rotate, immediate flush, stderr output for WARNING+
- **Thread-safe** — RLock on playlist, `call_from_thread` for all UI mutations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [VLC media player](https://www.videolan.org/vlc/) installed on your system

### Install & Run

```bash
# Clone
git clone https://github.com/diascii/tuneterm.git
cd tuneterm

# Virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -e .

# Run!
tuneterm
```

Or with a specific music directory:
```bash
tuneterm --dir "D:\Music"
```

Or play a file directly:
```bash
tuneterm play "D:\Music\song.mp3"
```

---

## ⌨️ Keybindings

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `n` | Next track |
| `p` | Previous track |
| `→` / `←` | Seek ±10s |
| `s` | Toggle Shuffle |
| `r` | Toggle Repeat |
| `t` | Cycle theme |
| `u` | Add URL (YouTube / stream) |
| `o` | Open folder |
| `/` | Search library |
| `e` | Equalizer |
| `?` | Help |
| `Ctrl+↑` / `Alt+↑` | Move track up in queue |
| `Ctrl+↓` / `Alt+↓` | Move track down in queue |
| `Delete` / `d` | Remove track from queue |
| `Tab` | Focus next widget |
| `q` | Quit |

---

## 🎨 Themes

Press **`t`** to cycle through **21 built-in themes**:

`textual-dark` · `textual-light` · `nord` · `gruvbox` · `catppuccin-mocha` · `catppuccin-latte` · `catppuccin-frappe` · `catppuccin-macchiato` · `dracula` · `tokyo-night` · `monokai` · `flexoki` · `solarized-dark` · `solarized-light` · `rose-pine` · `rose-pine-moon` · `rose-pine-dawn` · `atom-one-dark` · `atom-one-light` · `ansi-dark` · `ansi-light`

---

## 🧪 Tests

```bash
pytest tests/ -v --tb=short
```

144+ tests covering playback engine, playlist, streaming, UI state, concurrency, and stress scenarios.

---

## 📁 Project Structure

```
tuneterm/
├── tuneterm/
│   ├── cli.py                    # CLI entry point (click)
│   ├── ui/                       # Textual TUI widgets
│   │   ├── app.py                # Main app: compose, bindings, playback orchestration
│   │   ├── track_list.py         # Queue DataTable with reorder
│   │   ├── now_playing.py        # Current track display + visualizer
│   │   ├── visualizer.py         # FFT audio visualizer
│   │   ├── controls.py           # Playback control bar (seek, shuffle, repeat)
│   │   ├── lyrics_panel.py       # Synced lyrics display
│   │   ├── file_browser.py       # Local file browser
│   │   ├── search_modal.py       # Library search
│   │   ├── add_url_modal.py      # Add YouTube URL
│   │   ├── equalizer_panel.py    # 10-band EQ
│   │   ├── help_modal.py         # Keybindings help
│   │   ├── first_run.py          # First-run setup screen
│   │   ├── status_bar.py         # Bottom status bar
│   │   └── styles.tcss           # Textual CSS
│   ├── player/
│   │   ├── engine.py             # VLCAudioEngine
│   │   ├── playlist.py           # Thread-safe playlist
│   │   ├── crossfade.py          # Crossfader
│   │   ├── metadata.py           # Audio metadata extraction
│   │   ├── library.py            # SQLite music library
│   │   ├── equalizer.py          # EQ presets
│   │   └── streaming.py          # yt-dlp YouTube extraction
│   ├── integrations/
│   │   ├── discord_rpc.py        # Discord Rich Presence
│   │   ├── lastfm.py             # Last.fm scrobbler
│   │   └── lyrics_fetch.py       # LRCLIB + Lyrics.ovh fetcher
│   └── utils/
│       ├── config.py             # TOML config
│       ├── logger.py             # Rotating logger + watchdog
│       └── session.py            # Session persistence
├── tests/                        # 144+ tests
└── pyproject.toml
```

---

## 📝 Dependencies

- `python-vlc` — Audio playback via VLC
- `textual` — Terminal UI framework
- `mutagen` — Audio metadata reading
- `yt-dlp` — YouTube stream extraction
- `pypresence` — Discord Rich Presence
- `pylast` — Last.fm API
- `soundcard` + `numpy` — FFT audio visualizer
- `requests` — Lyrics API calls
- `click` — CLI argument parsing

---

## 📄 License

MIT
