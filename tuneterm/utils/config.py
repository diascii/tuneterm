import logging
import os
import tomllib
from pathlib import Path
from dataclasses import dataclass

_log = logging.getLogger("tuneterm")

CONFIG_DIR = Path.home() / ".config" / "tuneterm"
CONFIG_FILE = CONFIG_DIR / "config.toml"

@dataclass
class Config:
    music_dir: str = ""
    theme: str = "cyberpunk"
    volume: int = 100
    repeat_mode: int = 0
    shuffle: bool = False
    
    @classmethod
    def load(cls) -> 'Config':
        if not CONFIG_FILE.exists():
            return cls()
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception as e:
            _log.warning("[Config] Gagal load config, fallback ke default: %s", e)
            return cls()

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            # Basic toml writer for simple flat dataclass
            f.write(f'music_dir = "{self.music_dir.replace(chr(92), chr(92)+chr(92))}"\n')
            f.write(f'theme = "{self.theme}"\n')
            f.write(f'volume = {self.volume}\n')
            f.write(f'repeat_mode = {self.repeat_mode}\n')
            f.write(f'shuffle = {"true" if self.shuffle else "false"}\n')

config = Config.load()
