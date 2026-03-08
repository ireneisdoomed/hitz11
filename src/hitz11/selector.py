from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from .models import Entry
from .db import row_to_entry


def is_weekend(local_date: date) -> bool:
    return local_date.weekday() >= 5


def _fetch_entries(conn: sqlite3.Connection, query: str, params: tuple) -> list[Entry]:
    rows = conn.execute(query, params).fetchall()
    return [row_to_entry(row) for row in rows]


def pick_entry_for_day(
    conn: sqlite3.Connection,
    *,
    local_date: date,
    origin_key: str,
    language: str,
    recency_days: int,
    rng: random.Random | None = None,
) -> tuple[Entry | None, str]:
    rng = rng or random.Random()
    post_type = "recap" if is_weekend(local_date) else "daily"
    recent_cutoff = (local_date - timedelta(days=recency_days)).isoformat()
    bootstrap_query: str | None = None

    if post_type == "daily":
        candidate_query = """
            SELECT * FROM entries e
            WHERE e.origin_key = ? AND e.language = ?
              AND e.id NOT IN (SELECT entry_id FROM posts)
              AND e.id NOT IN (
                SELECT entry_id FROM posts WHERE post_date_local >= ?
              )
        """
        fallback_query = """
            SELECT * FROM entries e
            WHERE e.origin_key = ? AND e.language = ?
              AND e.id NOT IN (SELECT entry_id FROM posts)
        """
    else:
        candidate_query = """
            SELECT e.* FROM entries e
            JOIN posts p ON p.entry_id = e.id
            WHERE e.origin_key = ? AND e.language = ?
              AND e.id NOT IN (
                SELECT entry_id FROM posts WHERE post_date_local >= ?
              )
            GROUP BY e.id
        """
        fallback_query = """
            SELECT e.* FROM entries e
            JOIN posts p ON p.entry_id = e.id
            WHERE e.origin_key = ? AND e.language = ?
            GROUP BY e.id
        """
        bootstrap_query = """
            SELECT * FROM entries e
            WHERE e.origin_key = ? AND e.language = ?
              AND e.id NOT IN (SELECT entry_id FROM posts)
        """

    candidates = _fetch_entries(conn, candidate_query, (origin_key, language, recent_cutoff))
    if not candidates:
        candidates = _fetch_entries(conn, fallback_query, (origin_key, language))
    if not candidates and post_type == "recap" and bootstrap_query is not None:
        candidates = _fetch_entries(conn, bootstrap_query, (origin_key, language))
    if not candidates:
        return None, post_type
    return rng.choice(candidates), post_type
