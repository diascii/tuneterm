from textual.widgets import Static
from textual import events
from textual.message import Message
from textual.reactive import reactive


def format_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


class PlaybackControls(Static):
    position    = reactive(0.0)
    duration    = reactive(0.0)
    is_playing  = reactive(False)
    shuffle     = reactive(False)
    repeat      = reactive("OFF")
    volume      = reactive(100)
    track_num   = reactive(0)
    track_total = reactive(0)

    class SeekMessage(Message):
        def __init__(self, position: float) -> None:
            self.position = position
            super().__init__()

    class ToggleShuffleMessage(Message):
        pass

    class ToggleRepeatMessage(Message):
        pass

    def on_mount(self):
        self.update_display()

    def watch_position(self, _):   self.update_display()
    def watch_duration(self, _):   self.update_display()
    def watch_is_playing(self, _): self.update_display()
    def watch_shuffle(self, _):    self.update_display()
    def watch_repeat(self, _):     self.update_display()
    def watch_volume(self, _):     self.update_display()
    def watch_track_num(self, _):  self.update_display()
    def watch_track_total(self, _):self.update_display()

    # ── Rendering ─────────────────────────────────────────────────────

    def update_display(self):
        width = self.size.width if self.size.width > 0 else 80

        # ── Play / pause icon ──────────────────────────────────────────
        if self.is_playing:
            state_rich  = "[bold green]▶[/bold green]"
            state_plain = "▶"
        else:
            state_rich  = "[yellow]⏸[/yellow]"
            state_plain = "⏸"

        # ── Track counter ──────────────────────────────────────────────
        if self.track_total > 0:
            counter_rich  = f"[dim]♪[/dim] [bold cyan]{self.track_num}/{self.track_total}[/bold cyan]"
            counter_plain = f"♪ {self.track_num}/{self.track_total}"
        else:
            counter_rich  = ""
            counter_plain = ""

        # ── Time strings ───────────────────────────────────────────────
        pos_str = format_time(self.position)
        dur_str = format_time(self.duration)

        # ── Volume ─────────────────────────────────────────────────────
        v = self.volume
        if v == 0:
            vol_glyph = "🔇"
        elif v <= 50:
            vol_glyph = "🔉"
        else:
            vol_glyph = "🔊"
        vol_rich  = f"[bold]{vol_glyph}[/bold] [cyan]{v}%[/cyan]"
        vol_plain = f"_ {v}%"        # emoji treated as 1 col for estimate

        # ── Shuffle ────────────────────────────────────────────────────
        if self.shuffle:
            shuf_rich  = "[bold green]⇄[/bold green]"
        else:
            shuf_rich  = "[grey37]⇄[/grey37]"
        shuf_plain = "⇄"

        # ── Repeat ─────────────────────────────────────────────────────
        if self.repeat == "OFF":
            rep_rich  = "[grey37]↻[/grey37]"
            rep_plain = "↻"
        elif self.repeat == "ONE":
            rep_rich  = "[bold green]¹↻[/bold green]"
            rep_plain = "¹↻"
        else:                        # ALL
            rep_rich  = "[bold green]↻ ALL[/bold green]"
            rep_plain = "↻ ALL"

        # ── Bar width ──────────────────────────────────────────────────
        # Left:  " ▶  ♪ 3/14  01:23 "
        # Right: " 03:00   🔊 75%   ⇄   ↻ ALL "
        left_plain  = f" {state_plain}  {counter_plain}  {pos_str} " if counter_plain \
                      else f" {state_plain}  {pos_str} "
        right_plain = f" {dur_str}   {vol_plain}   {shuf_plain}   {rep_plain} "

        bar_width = max(8, width - len(left_plain) - len(right_plain))

        # ── Progress fill ──────────────────────────────────────────────
        progress = (self.position / self.duration) if self.duration > 0 else 0.0
        filled   = int(progress * bar_width)
        empty    = bar_width - filled

        # Thumb character on the leading edge when playing
        if self.is_playing and 0 < filled < bar_width:
            bar = (
                f"[cyan]{'━' * (filled - 1)}[/cyan]"
                f"[bold cyan]╸[/bold cyan]"
                f"[grey30]{'━' * empty}[/grey30]"
            )
        else:
            bar = f"[cyan]{'━' * filled}[/cyan][grey30]{'━' * empty}[/grey30]"

        # ── Assemble ───────────────────────────────────────────────────
        left = (
            f" {state_rich}  {counter_rich}  {pos_str} "
            if counter_plain else f" {state_rich}  {pos_str} "
        )
        right = f" {dur_str}   {vol_rich}   {shuf_rich}   {rep_rich} "

        self.update(left + bar + right)

        # Store geometry for click handling
        self._bar_start   = len(left_plain)
        self._bar_width   = bar_width
        # Shuffle starts after bar + dur_str + vol
        base_right        = len(left_plain) + bar_width
        dur_vol_len       = len(f" {dur_str}   {vol_plain}   ")
        self._shuffle_col = base_right + dur_vol_len
        self._repeat_col  = self._shuffle_col + len(shuf_plain) + 3  # "⇄   "

    # ── Seek / toggle on click ─────────────────────────────────────────

    def on_click(self, event: events.Click) -> None:
        if not hasattr(self, "_bar_start"):
            return

        x = event.x

        # Repeat zone
        if hasattr(self, "_repeat_col") and x >= self._repeat_col:
            self.post_message(self.ToggleRepeatMessage())
            return

        # Shuffle zone
        if hasattr(self, "_shuffle_col") and x >= self._shuffle_col:
            self.post_message(self.ToggleShuffleMessage())
            return

        # Progress bar zone
        if self.duration > 0 and self._bar_start <= x <= self._bar_start + self._bar_width:
            pct     = (x - self._bar_start) / self._bar_width
            new_pos = max(0.0, min(1.0, pct)) * self.duration
            self.post_message(self.SeekMessage(new_pos))
