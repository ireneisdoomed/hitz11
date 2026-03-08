import random
import sqlite3
from datetime import date

from hitz11.db import init_db, mark_post_sent, upsert_entry
from hitz11.selector import pick_entry_for_day


def _seed_entries(conn: sqlite3.Connection):
    upsert_entry(
        conn,
        word="Oasis",
        definition="Sitio con agua",
        etymology_text="texto oasis",
        origin_key="basque",
        language="es",
        source_url="https://example.test/a",
    )
    upsert_entry(
        conn,
        word="Obito",
        definition="Fallecimiento",
        etymology_text="texto obito",
        origin_key="basque",
        language="es",
        source_url="https://example.test/b",
    )
    upsert_entry(
        conn,
        word="Orca",
        definition="Mamifero marino",
        etymology_text="texto orca",
        origin_key="basque",
        language="es",
        source_url="https://example.test/c",
    )
    conn.commit()


def test_weekday_uses_unposted_entries():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed_entries(conn)

    # Mark one entry as posted.
    posted_id = conn.execute("SELECT id FROM entries WHERE word = 'Oasis'").fetchone()["id"]
    mark_post_sent(
        conn,
        entry_id=posted_id,
        local_date=date(2026, 3, 1),
        post_type="daily",
        telegram_chat_id="@x",
        telegram_message_id="1",
    )

    entry, post_type = pick_entry_for_day(
        conn,
        local_date=date(2026, 3, 2),  # Monday
        origin_key="basque",
        language="es",
        recency_days=30,
        rng=random.Random(1),
    )

    assert post_type == "daily"
    assert entry is not None
    assert entry.word in {"Obito", "Orca"}


def test_weekend_uses_already_posted_entries():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed_entries(conn)

    posted_id = conn.execute("SELECT id FROM entries WHERE word = 'Oasis'").fetchone()["id"]
    mark_post_sent(
        conn,
        entry_id=posted_id,
        local_date=date(2026, 2, 1),
        post_type="daily",
        telegram_chat_id="@x",
        telegram_message_id="1",
    )

    entry, post_type = pick_entry_for_day(
        conn,
        local_date=date(2026, 3, 8),  # Sunday
        origin_key="basque",
        language="es",
        recency_days=30,
        rng=random.Random(2),
    )

    assert post_type == "recap"
    assert entry is not None
    assert entry.word == "Oasis"


def test_weekend_bootstraps_with_unposted_if_no_history():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed_entries(conn)

    entry, post_type = pick_entry_for_day(
        conn,
        local_date=date(2026, 3, 8),  # Sunday
        origin_key="basque",
        language="es",
        recency_days=30,
        rng=random.Random(2),
    )

    assert post_type == "recap"
    assert entry is not None
    assert entry.word in {"Oasis", "Obito", "Orca"}
