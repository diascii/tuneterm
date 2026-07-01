from dataclasses import dataclass

@dataclass
class ThemeColors:
    background: str
    primary: str
    secondary: str
    accent: str
    viz_gradient: list[str]

THEMES = {
    "cyberpunk": ThemeColors("#0a0a0f", "#ff2d7b", "#00f0ff", "#bf40ff", ["#00f0ff", "#ff2d7b", "#bf40ff"]),
    "nord": ThemeColors("#2e3440", "#88c0d0", "#a3be8c", "#eceff4", ["#81a1c1", "#88c0d0", "#8fbcbb"]),
    "gruvbox": ThemeColors("#282828", "#fabd2f", "#8ec07c", "#fe8019", ["#b8bb26", "#fabd2f", "#fe8019"]),
    "catppuccin": ThemeColors("#1e1e2e", "#cba6f7", "#94e2d5", "#f5c2e7", ["#94e2d5", "#cba6f7", "#f5c2e7"]),
}
