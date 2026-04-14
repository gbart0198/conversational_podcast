import sqlite3
import os
from pathlib import Path

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/podcast.db")


def get_connection() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS talks (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'created',
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sources (
                id          TEXT PRIMARY KEY,
                talk_id     TEXT NOT NULL REFERENCES talks(id) ON DELETE CASCADE,
                type        TEXT NOT NULL,
                content     TEXT NOT NULL,
                embedding   TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS script_segments (
                id          TEXT PRIMARY KEY,
                talk_id     TEXT NOT NULL REFERENCES talks(id) ON DELETE CASCADE,
                position    INTEGER NOT NULL,
                speaker     TEXT NOT NULL,
                text        TEXT NOT NULL,
                audio_file  TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id              TEXT PRIMARY KEY,
                talk_id         TEXT NOT NULL REFERENCES talks(id) ON DELETE CASCADE,
                segment_index   INTEGER NOT NULL,
                question        TEXT NOT NULL,
                answer          TEXT NOT NULL,
                audio_file      TEXT,
                created_at      TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
