from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from .models import Entry


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word TEXT NOT NULL,
  definition TEXT NOT NULL,
  etymology_text TEXT NOT NULL,
  origin_key TEXT NOT NULL,
  language TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(word, origin_key, language)
);

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER NOT NULL REFERENCES entries(id),
  post_date_local TEXT NOT NULL,
  post_type TEXT NOT NULL CHECK(post_type IN ('daily', 'recap')),
  telegram_chat_id TEXT NOT NULL,
  telegram_message_id TEXT,
  sent_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(post_date_local)
);

CREATE TABLE IF NOT EXISTS engagement_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER NOT NULL REFERENCES entries(id),
  post_id INTEGER REFERENCES posts(id),
  snapshot_at TEXT NOT NULL DEFAULT (datetime('now')),
  reactions_count INTEGER,
  comments_count INTEGER,
  views_count INTEGER,
  forwards_count INTEGER,
  raw_payload TEXT
);

CREATE TABLE IF NOT EXISTS run_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_type TEXT NOT NULL,
  status TEXT NOT NULL,
  details TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_posts_entry_id ON posts(entry_id);
CREATE INDEX IF NOT EXISTS idx_entries_origin ON entries(origin_key, language);
"""


@contextmanager
def connect(db_path: str | Path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def upsert_entry(
    conn: sqlite3.Connection,
    *,
    word: str,
    definition: str,
    etymology_text: str,
    origin_key: str,
    language: str,
    source_url: str,
) -> None:
    source_hash = hashlib.sha256(etymology_text.encode("utf-8")).hexdigest()
    conn.execute(
        """
        INSERT INTO entries (word, definition, etymology_text, origin_key, language, source_url, source_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(word, origin_key, language)
        DO UPDATE SET
          definition=excluded.definition,
          etymology_text=excluded.etymology_text,
          source_url=excluded.source_url,
          source_hash=excluded.source_hash,
          updated_at=datetime('now')
        """,
        (word, definition, etymology_text, origin_key, language, source_url, source_hash),
    )


def already_posted_today(conn: sqlite3.Connection, *, local_date: date) -> bool:
    row = conn.execute(
        "SELECT 1 FROM posts WHERE post_date_local = ? LIMIT 1",
        (local_date.isoformat(),),
    ).fetchone()
    return row is not None


def mark_post_sent(
    conn: sqlite3.Connection,
    *,
    entry_id: int,
    local_date: date,
    post_type: str,
    telegram_chat_id: str,
    telegram_message_id: str,
) -> None:
    conn.execute(
        """
        INSERT INTO posts (entry_id, post_date_local, post_type, telegram_chat_id, telegram_message_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            local_date.isoformat(),
            post_type,
            telegram_chat_id,
            telegram_message_id,
        ),
    )
    conn.commit()


def log_run(conn: sqlite3.Connection, *, run_type: str, status: str, details: str = "") -> None:
    conn.execute(
        "INSERT INTO run_log (run_type, status, details) VALUES (?, ?, ?)",
        (run_type, status, details),
    )
    conn.commit()


def row_to_entry(row: sqlite3.Row) -> Entry:
    return Entry(
        id=row["id"],
        word=row["word"],
        definition=row["definition"],
        etymology_text=row["etymology_text"],
        origin_key=row["origin_key"],
        language=row["language"],
        source_url=row["source_url"],
    )
