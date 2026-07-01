import logging
import sqlite3
import os
import contextlib
import threading
from pathlib import Path
from tuneterm.player.metadata import TrackInfo, extract_metadata
from tuneterm.utils.config import CONFIG_DIR

_log = logging.getLogger("tuneterm")

DB_PATH = CONFIG_DIR / "library.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class Library:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    @contextlib.contextmanager
    def _db_conn(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._db_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    filepath TEXT PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    year TEXT,
                    genre TEXT,
                    duration REAL
                )
            """)
            conn.commit()

    def scan_directory(self, path: str):
        thread = threading.Thread(target=self._scan_directory_worker, args=(path,), daemon=True)
        thread.start()

    def _scan_directory_worker(self, path: str):
        batch = []
        for root, _, files in os.walk(path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]:
                    filepath = os.path.join(root, file)
                    try:
                        info = extract_metadata(filepath)
                        batch.append(info)
                    except Exception as e:
                        _log.warning("[Library] Gagal extract metadata %s: %s", filepath, e)
                        continue
                    
                    if len(batch) >= 100:
                        self._save_batch(batch)
                        batch = []
        if batch:
            self._save_batch(batch)

    def _save_batch(self, batch):
        with self._db_conn() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO tracks 
                (filepath, title, artist, album, year, genre, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                (info.filepath, info.title, info.artist, info.album, info.year, info.genre, info.duration)
                for info in batch
            ])
            conn.commit()

    def add_track(self, info: TrackInfo):
        with self._db_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tracks 
                (filepath, title, artist, album, year, genre, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (info.filepath, info.title, info.artist, info.album, info.year, info.genre, info.duration))
            conn.commit()

    def search(self, query: str) -> list[TrackInfo]:
        q = f"%{query}%"
        with self._db_conn() as conn:
            cursor = conn.execute("""
                SELECT filepath, title, artist, album, year, genre, duration
                FROM tracks
                WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
                LIMIT 50
            """, (q, q, q))
            
            results = []
            for row in cursor.fetchall():
                results.append(TrackInfo(
                    filepath=row[0], title=row[1], artist=row[2], 
                    album=row[3], year=row[4], genre=row[5], 
                    duration=row[6], bitrate=0, sample_rate=0, format=""
                ))
            return results

