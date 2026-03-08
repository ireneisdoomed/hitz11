from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import load_settings
from .crawler import crawl_all_letters
from .db import (
    already_posted_today,
    connect,
    init_db,
    log_run,
    mark_post_sent,
    upsert_entry,
)
from .selector import pick_entry_for_day
from .telegram_client import compose_message, send_message


def _now_in_timezone(tz_name: str) -> datetime:
    return datetime.now(tz=ZoneInfo(tz_name))


def run_crawl(db_path: Path, base_url: str, origin_key: str, language: str) -> int:
    entries = crawl_all_letters(base_url=base_url)
    with connect(db_path) as conn:
        init_db(conn)
        for item in entries:
            upsert_entry(
                conn,
                word=item.word,
                definition=item.definition,
                etymology_text=item.etymology_text,
                origin_key=origin_key,
                language=language,
                source_url=item.source_url,
            )
        conn.commit()
        log_run(conn, run_type="crawl", status="ok", details=f"upserted={len(entries)}")
    return len(entries)


def run_post(
    db_path: Path,
    *,
    dry_run: bool,
    skip_time_check: bool,
    expected_time: str,
) -> int:
    settings = load_settings(require_telegram=not dry_run)
    now_local = _now_in_timezone(settings.timezone)
    local_date = now_local.date()

    if not skip_time_check:
        current_hhmm = now_local.strftime("%H:%M")
        if current_hhmm != expected_time:
            print(f"Skip: local time is {current_hhmm}, expected {expected_time}")
            return 0

    with connect(db_path) as conn:
        init_db(conn)
        if already_posted_today(conn, local_date=local_date):
            print(f"Skip: already posted for {local_date.isoformat()}")
            return 0

        entry, post_type = pick_entry_for_day(
            conn,
            local_date=local_date,
            origin_key=settings.origin_key,
            language=settings.language,
            recency_days=settings.recency_days,
        )
        if entry is None:
            log_run(conn, run_type="post", status="empty", details="no candidates")
            print("No candidate entries available")
            return 0

        message = compose_message(entry, post_type)
        if dry_run:
            print(message)
            log_run(
                conn,
                run_type="post",
                status="dry_run",
                details=f"entry_id={entry.id};post_type={post_type}",
            )
            return 0

        message_id = send_message(
            token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=message,
        )
        mark_post_sent(
            conn,
            entry_id=entry.id,
            local_date=local_date,
            post_type=post_type,
            telegram_chat_id=settings.telegram_chat_id,
            telegram_message_id=message_id,
        )
        log_run(
            conn,
            run_type="post",
            status="ok",
            details=f"entry_id={entry.id};post_type={post_type};message_id={message_id}",
        )
    print(f"Posted {post_type}: {entry.word} (message_id={message_id})")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hitz11 daily Telegram publisher")
    parser.add_argument("--db-path", default="hitz11.db", help="Path to SQLite DB")

    sub = parser.add_subparsers(dest="command", required=True)

    crawl_cmd = sub.add_parser("crawl", help="Crawl source pages and upsert entries")
    crawl_cmd.add_argument(
        "--base-url",
        default="https://josecanovas.com/diccionarioetimologico",
        help="Base URL of the dictionary pages",
    )

    post_cmd = sub.add_parser("post", help="Pick and send one message to Telegram")
    post_cmd.add_argument("--dry-run", action="store_true", help="Print message without sending")
    post_cmd.add_argument(
        "--skip-time-check",
        action="store_true",
        help="Allow posting regardless of local time",
    )
    post_cmd.add_argument(
        "--expected-time",
        default="11:11",
        help="Expected local HH:MM if time check is enabled",
    )

    daily_cmd = sub.add_parser("daily", help="Crawl and then post")
    daily_cmd.add_argument("--dry-run", action="store_true", help="Print message without sending")
    daily_cmd.add_argument(
        "--skip-time-check",
        action="store_true",
        help="Allow posting regardless of local time",
    )
    daily_cmd.add_argument(
        "--expected-time",
        default="11:11",
        help="Expected local HH:MM if time check is enabled",
    )
    daily_cmd.add_argument(
        "--base-url",
        default="https://josecanovas.com/diccionarioetimologico",
        help="Base URL of the dictionary pages",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)

    if args.command == "crawl":
        settings = load_settings(require_telegram=False)
        count = run_crawl(
            db_path,
            base_url=args.base_url,
            origin_key=settings.origin_key,
            language=settings.language,
        )
        print(f"Crawl complete. Upserted {count} entries")
        return 0

    if args.command == "post":
        return run_post(
            db_path,
            dry_run=args.dry_run,
            skip_time_check=args.skip_time_check,
            expected_time=args.expected_time,
        )

    if args.command == "daily":
        settings = load_settings(require_telegram=False)
        count = run_crawl(
            db_path,
            base_url=args.base_url,
            origin_key=settings.origin_key,
            language=settings.language,
        )
        print(f"Crawl complete. Upserted {count} entries")
        return run_post(
            db_path,
            dry_run=args.dry_run,
            skip_time_check=args.skip_time_check,
            expected_time=args.expected_time,
        )

    raise SystemExit("Unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
