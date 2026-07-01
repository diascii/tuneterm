from textual.app import App, ComposeResult
from textual.theme import BUILTIN_THEMES
from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane
from tuneterm.ui.file_browser import FileBrowser
from tuneterm.ui.track_list import TrackList
from tuneterm.ui.now_playing import NowPlaying
from tuneterm.ui.status_bar import StatusBar
from tuneterm.ui.controls import PlaybackControls, format_time
from tuneterm.ui.first_run import FirstRunScreen
from tuneterm.player.engine import VLCAudioEngine
from tuneterm.player.crossfade import Crossfader
from tuneterm.player.playlist import Playlist
from tuneterm.utils.config import config
from tuneterm.player.library import Library
import logging
import sys

_log = logging.getLogger("tuneterm")

def _set_terminal_title(title: str):
    """Set window title — uses Win32 API on Windows, ANSI escape elsewhere."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass
    else:
        # Fallback ANSI escape (handled by Textual on most terminals)
        print(f"\x1b]0;{title}\x07", end="", flush=True)

class TuneTermApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "TuneTerm"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "play_pause", "Play/Pause"),
        ("n", "next_track", "Next"),
        ("p", "prev_track", "Previous"),
        ("right", "seek_forward", "Seek +10s"),
        ("left", "seek_backward", "Seek -10s"),
        ("s", "toggle_shuffle", "Shuffle"),
        ("r", "toggle_repeat", "Repeat"),
        ("tab", "focus_next", "Focus Next"),
        ("u", "add_url", "Add URL"),
        ("o", "change_dir", "Open Folder"),
        ("/", "search", "Search"),
        ("e", "equalizer", "Equalizer"),
        ("t", "cycle_theme", "Theme"),
        ("?", "help", "Help"),
    ]

    def __init__(self, music_dir=None, play_on_start=None):
        super().__init__()
        self.music_dir = music_dir or config.music_dir
        self.play_on_start = play_on_start
        self.engine = VLCAudioEngine()
        self.playlist = Playlist()
        self.library = Library()
        self.crossfader = Crossfader(self.engine)
        
        self._was_playing = False
        self._title_text = ""
        self._marquee_offset = 0
        self._marquee_max_w = 35  # typical tab width
        self._theme_list = list(BUILTIN_THEMES.keys())
        self._theme_idx = self._theme_list.index("nord") if "nord" in self._theme_list else 0
        
    def compose(self) -> ComposeResult:
        from tuneterm.ui.lyrics_panel import LyricsPanel
        with Horizontal():
            # Left panel
            with Vertical(id="left-panel"):
                yield FileBrowser(id="file-browser")
            
            # Right panel
            with Vertical(id="right-panel"):
                yield NowPlaying(id="now-playing")
                with TabbedContent(id="tabs"):
                    with TabPane("Queue", id="queue-tab"):
                        yield TrackList(id="track-list")
                    with TabPane("Lyrics", id="lyrics-tab"):
                        yield LyricsPanel(id="lyrics-panel")
                 
        # Bottom controls
        yield PlaybackControls(id="playback-controls")
        yield Footer()

    def on_mount(self) -> None:
        from tuneterm.integrations.discord_rpc import DiscordRPC
        from tuneterm.integrations.lastfm import LastFMScrobbler
        self.rpc = DiscordRPC()
        self.scrobbler = LastFMScrobbler()
        self.run_worker(self._connect_rpc, thread=True)
        
        self.set_interval(0.5, self._tick_playback)
        self.set_interval(15.0, self._update_discord_rpc) # Update discord every 15s to respect rate limits
        self.set_interval(30.0, self._watchdog_check)     # Watchdog — heartbeat log tiap 30 detik
        self.set_interval(0.5, self._tick_marquee)        # Marquee — sliding title tiap 0.5 detik
        
        # Set default theme
        initial_theme = self._theme_list[self._theme_idx]
        self.theme = initial_theme
        try:
            sb = self.query_one(StatusBar)
            sb.theme_name = initial_theme
        except Exception:
            pass
        
        if not self.music_dir:
            self.push_screen(FirstRunScreen())
        else:
            self.load_music_dir(self.music_dir)
            
        if self.play_on_start:
            self.load_and_play_start_file()

    def _watchdog_check(self):
        """Heartbeat — cek kalo main thread masih responsif. Log timestamp."""
        _log.debug("[WATCHDOG] Heartbeat OK")

    def _connect_rpc(self):
        try:
            self.rpc.connect()
        except Exception as e:
            _log.warning("[DiscordRPC] Gagal connect: %s", e)

    @work(thread=True)
    def _update_discord_rpc(self):
        if not hasattr(self, 'rpc') or not self.rpc.connected:
            return
            
        track = self.playlist.current()
        if track and self.engine.is_playing():
            details = f"{track.title}"
            state = f"by {track.artist}"
            
            # Fetch album art URL from iTunes Search API in the background if no thumb_url exists
            large_image = None
            if hasattr(track, 'thumb_url') and track.thumb_url:
                large_image = track.thumb_url
            else:
                try:
                    import urllib.request, urllib.parse, json
                    query = urllib.parse.quote(f"{track.artist} {track.title}")
                    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    resp = urllib.request.urlopen(req, timeout=3).read()
                    data = json.loads(resp)
                    if data['results']:
                        # Get 512x512 image instead of 100x100
                        large_image = data['results'][0]['artworkUrl100'].replace('100x100bb', '512x512bb')
                except Exception as e:
                    _log.warning("[App] Gagal fetch iTunes art: %s", e)
            # Fallback public music icon if no album art found
            if not large_image:
                large_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Music_1_-_The_Noun_Project.svg/512px-Music_1_-_The_Noun_Project.svg.png"
        else:
            details = "Idling"
            state = "Looking for music"
            # Public music icon as fallback when no album art
            large_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Music_1_-_The_Noun_Project.svg/512px-Music_1_-_The_Noun_Project.svg.png"
            
        try:
            self.rpc.update(details, state, large_image=large_image)
        except Exception as e:
            _log.warning("[DiscordRPC] Gagal update presence: %s", e)

    @work(thread=True)
    def load_and_play_start_file(self):
        with self.playlist._lock:
            info = self.playlist.add(self.play_on_start)
        self.call_from_thread(self._on_start_track_added, info)

    def _on_start_track_added(self, info):
        track_list = self.query_one(TrackList)
        track_list.add_row(info.title, info.artist, info.album, format_time(info.duration))
        self.play_track(0)
        
    def update_playback_status(self):
        try:
            controls = self.query_one(PlaybackControls)
            pos = self.engine.get_position()
            controls.position = pos
            controls.duration = self.engine.get_duration()
            controls.is_playing = self.engine.is_playing()
            controls.shuffle = self.playlist.is_shuffled
            controls.repeat = self.playlist.repeat_mode.name
            
            vis = self.query_one("Visualizer")
            if hasattr(vis, "is_playing"):
                vis.is_playing = self.engine.is_playing()
            
            # Update status bar
            try:
                sb = self.query_one(StatusBar)
                sb.track_count = len(self.playlist.tracks)
                sb.shuffle = self.playlist.is_shuffled
                sb.repeat = self.playlist.repeat_mode.name
            except Exception:
                pass
                
            # Update lyrics
            try:
                lyrics_panel = self.query_one("#lyrics-panel")
                lyrics_panel.update_position(pos)
            except Exception as e:
                _log.warning("[App] Gagal update posisi lyrics: %s", e)
        except Exception as e:
            _log.warning("[App] Gagal update playback status: %s", e)

    def load_music_dir(self, path: str):
        self.music_dir = path
        browser = self.query_one(FileBrowser)
        browser.load_directory(path)
        self.library.scan_directory(path)


    def action_next_track(self):
        self.scrobble_current_track()
        track = self.playlist.next()
        if track:
            # Crossfade: fade out current → play next → fade in
            self.crossfader.crossfade_out(on_done=lambda: self._play_next_with_fadein(track))
        else:
            self.reset_now_playing()

    def _play_next_with_fadein(self, track):
        """Play track and fade in (called after fade-out completes)."""
        self.call_from_thread(self._do_fadein_play, track)

    def _do_fadein_play(self, track):
        """Actually play and fade in (called on main thread)."""
        self.engine.play(track.filepath)
        self.update_now_playing()
        self.crossfader.crossfade_in()
        self.bg_update_now_playing(track.artist, track.title)

    def action_prev_track(self):
        self.scrobble_current_track()
        track = self.playlist.previous()
        if track:
            self.engine.play(track.filepath)
            self.update_now_playing()
            self.crossfader.crossfade_in()
            self.bg_update_now_playing(track.artist, track.title)
        else:
            self.reset_now_playing()

    def action_seek_forward(self):
        self.engine.seek_relative(10)
        
    def action_seek_backward(self):
        self.engine.seek_relative(-10)
        
    def action_toggle_shuffle(self):
        self.playlist.toggle_shuffle()
        self.update_playback_status()
        
    def action_toggle_repeat(self):
        self.playlist.toggle_repeat()
        self.update_playback_status()
        
    def on_playback_controls_seek_message(self, event) -> None:
        self.engine.seek_absolute(event.position)
        
    def on_playback_controls_toggle_shuffle_message(self, event) -> None:
        self.action_toggle_shuffle()
        
    def on_playback_controls_toggle_repeat_message(self, event) -> None:
        self.action_toggle_repeat()

    def action_add_url(self):
        from tuneterm.ui.add_url_modal import AddUrlModal
        self.push_screen(AddUrlModal())

    @work(thread=True)
    def add_url_and_play(self, url: str):
        with self.playlist._lock:
            info = self.playlist.add(url)
        self.call_from_thread(self._on_url_track_added, info)

    def _on_url_track_added(self, info):
        track_list = self.query_one(TrackList)
        track_list.add_row(info.title, info.artist, info.album, format_time(info.duration))
        try:
            with self.playlist._lock:
                added_idx = self.playlist._tracks.index(info)
            self.play_track(added_idx)
        except ValueError:
            pass

    def action_change_dir(self):
        from tuneterm.ui.first_run import FirstRunScreen
        self.push_screen(FirstRunScreen())

    def _check_track_end(self):
        """Poll-based track end detection — aman karena di main thread."""
        try:
            is_playing = self.engine.is_playing()
            was_playing = self._was_playing
            self._was_playing = is_playing
            
            # Detect transition: was playing → now stopped
            if was_playing and not is_playing:
                track = self.playlist.current()
                if track is not None:
                    # Check position — near end? skip if user manually paused
                    pos = self.engine.get_position()
                    dur = self.engine.get_duration()
                    _log.debug("[App] Track end detected: pos=%s, dur=%s", pos, dur)
                    
                    if dur > 0 and pos >= dur * 0.8:  # 80%+ means track ended naturally
                        _log.info("[App] Track end detected, crossfading to next")
                        self.scrobble_current_track()
                        track = self.playlist.next()
                        if track:
                            self.crossfader.crossfade_out(on_done=lambda: self._play_next_with_fadein(track))
                        else:
                            self.reset_now_playing()
        except Exception as e:
            _log.error("[App] _check_track_end error: %s", e)

    def _tick_marquee(self):
        """Sliding title effect — geser title kalo kepanjangan buat tab."""
        if not self._title_text or len(self._title_text) <= self._marquee_max_w:
            return  # ga perlu geser
        self._marquee_offset += 1
        # Loop — pas sampe ujung, balik ke awal
        if self._marquee_offset >= len(self._title_text):
            self._marquee_offset = 0
        # Potong visible portion
        end = self._marquee_offset + self._marquee_max_w
        visible = self._title_text[self._marquee_offset:end]
        if len(visible) < self._marquee_max_w:
            # Tambah spacing terus sisa dari depan biar transisi mulus
            remainder = self._marquee_max_w - len(visible)
            visible += " --- " + self._title_text[:remainder]
        _set_terminal_title(visible)

    def _tick_playback(self):
        """Tick yang menggabungkan update status + track end check."""
        self._check_track_end()
        self.update_playback_status()
        
    def play_track(self, index: int):
        if 0 <= index < len(self.playlist.tracks):
            self.scrobble_current_track()
            self.playlist.current_index = index
            track = self.playlist.tracks[index]
            self.engine.stop()  # Cleanup VLC state before playing new track
            self.engine.play(track.filepath)
            self.update_now_playing()
            self.crossfader.crossfade_in()
            self.bg_update_now_playing(track.artist, track.title)

    def update_now_playing(self):
        track = self.playlist.current()
        if track:
            np = self.query_one(NowPlaying)
            np.update_track(track.title, track.artist, track.album, None)
            np.set_playing(True)
            
            # Set terminal title to current track
            self._title_text = f"{track.artist} - {track.title} | TuneTerm"
            self._marquee_offset = 0
            self.title = self._title_text
            # Tampilkan awal title dulu
            if len(self._title_text) > self._marquee_max_w:
                _set_terminal_title(self._title_text[:self._marquee_max_w])
            else:
                _set_terminal_title(self._title_text)
            
            # Lyrics: try local .lrc first (instant), else bg fetch from web
            try:
                lyrics_panel = self.query_one("#lyrics-panel")
                if not lyrics_panel.try_load_local_lrc(track.filepath):
                    lyrics_panel.update("Loading lyrics...")
                    self.run_worker(self._bg_fetch_lyrics, thread=True)
            except Exception:
                pass
            self.run_worker(self._bg_load_cover_art, thread=True)

    def reset_now_playing(self):
        """Reset UI when playback ends (no more tracks in queue)."""
        np = self.query_one(NowPlaying)
        np.update_track("Playback finished", "", "", None)
        np.set_playing(False)
        self._title_text = ""
        self._marquee_offset = 0
        self.title = "TuneTerm"
        _set_terminal_title("TuneTerm")

    @work(thread=True)
    def _bg_load_cover_art(self):
        from tuneterm.player.metadata import extract_cover_art
        track = self.playlist.current()
        if not track:
            return
        if hasattr(track, 'cover_art_bytes') and track.cover_art_bytes:
            cover_art_bytes = track.cover_art_bytes
        else:
            cover_art_bytes = extract_cover_art(track.filepath)
            
        def apply_art():
            current_track = self.playlist.current()
            if current_track and current_track.filepath == track.filepath:
                np = self.query_one(NowPlaying)
                np.update_track(track.title, track.artist, track.album, cover_art_bytes)
                
        self.call_from_thread(apply_art)

    @work(thread=True)
    def _bg_fetch_lyrics(self):
        """Fetch lyrics in background thread — jangan block main thread."""
        track = self.playlist.current()
        if not track or not track.artist or not track.title:
            return
        from tuneterm.integrations.lyrics_fetch import fetch_lyrics_from_web
        content = fetch_lyrics_from_web(track.artist, track.title)
        def update_panel():
            try:
                lp = self.query_one("#lyrics-panel")
                lp.display_web_lyrics(content)
            except Exception as e:
                _log.warning("[App] Gagal update panel lirik: %s", e)
        self.call_from_thread(update_panel)

    def action_play_pause(self):
        self.engine.toggle_pause()
        np = self.query_one(NowPlaying)
        np.set_playing(self.engine.is_playing())

    def on_file_browser_file_selected_message(self, event: FileBrowser.FileSelectedMessage) -> None:
        self.handle_file_selection(event.filepath)

    @work(thread=True)
    def handle_file_selection(self, filepath: str):
        with self.playlist._lock:
            info = self.playlist.add(filepath)
        self.call_from_thread(self._on_file_track_added, info)

    def _on_file_track_added(self, info):
        track_list = self.query_one(TrackList)
        track_list.add_row(info.title, info.artist, info.album, format_time(info.duration))

    def on_track_list_track_selected_message(self, event: TrackList.TrackSelectedMessage) -> None:
        self.play_track(event.index)
        
    def on_track_list_track_deleted_message(self, event: TrackList.TrackDeletedMessage) -> None:
        self.playlist.remove(event.index)
        
        # We must completely redraw the track list to prevent index shifting bugs
        track_list = self.query_one(TrackList)
        track_list.clear()
        for info in self.playlist.tracks:
            track_list.add_row(info.title, info.artist, info.album, format_time(info.duration))

    def on_track_list_track_moved_message(self, event: TrackList.TrackMovedMessage) -> None:
        """Handle move track up/down from TrackList."""
        success = self.playlist.move_track(event.from_index, event.to_index)
        if success:
            # Redraw track list
            track_list = self.query_one(TrackList)
            track_list.clear()
            for info in self.playlist.tracks:
                track_list.add_row(info.title, info.artist, info.album, format_time(info.duration))
            # Move cursor to new position
            track_list.move_cursor(row=event.to_index)

    def action_search(self):
        from tuneterm.ui.search_modal import SearchModal
        self.push_screen(SearchModal())

    def action_equalizer(self):
        from tuneterm.ui.equalizer_panel import EqualizerPanel
        self.push_screen(EqualizerPanel())

    def action_cycle_theme(self):
        """Cycle to next Textual built-in theme."""
        self._theme_idx = (self._theme_idx + 1) % len(self._theme_list)
        theme_name = self._theme_list[self._theme_idx]
        self.theme = theme_name
        self.notify(f"Theme: [bold]{theme_name}[/bold]")
        # Update status bar
        try:
            sb = self.query_one(StatusBar)
            sb.theme_name = theme_name
        except Exception:
            pass
        _log.info("[Theme] Switched to %s", theme_name)

    def action_help(self):
        from tuneterm.ui.help_modal import HelpModal
        self.push_screen(HelpModal())

    def play_from_search(self, track):
        self.playlist.add_track_info(track)
        track_list = self.query_one(TrackList)
        track_list.add_row(track.title, track.artist, track.album, format_time(track.duration))
        self.play_track(len(self.playlist.tracks) - 1)

    def query_library(self, query: str):
        return self.library.search(query)

    def scrobble_current_track(self):
        import time
        track = self.playlist.current()
        if track:
            self.bg_scrobble(track.artist, track.title, int(time.time()))

    @work(thread=True)
    def bg_update_now_playing(self, artist: str, title: str):
        if hasattr(self, 'scrobbler') and self.scrobbler:
            self.scrobbler.update_now_playing(artist, title)

    @work(thread=True)
    def bg_scrobble(self, artist: str, title: str, timestamp: int):
        if hasattr(self, 'scrobbler') and self.scrobbler:
            self.scrobbler.scrobble(artist, title, timestamp)

