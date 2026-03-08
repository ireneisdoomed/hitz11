# Hitz11

Hitz11 is a small daily etymology publisher for Telegram channels.

- Source crawl: DEEILE pages from josecanovas.com
- Storage: SQLite
- Selection: random word of the day
- Weekend mode: recap from already posted words
- Scheduler: GitHub Actions at 11:11 Europe/Madrid

## 1) Requirements

- Python 3.11+
- uv

## 2) Local setup

```bash
uv sync --extra dev
cp .env.example .env
```

Fill `.env` with your real Telegram values.

## 3) Run locally

Crawl and update DB:

```bash
uv run hitz11 --db-path hitz11.db crawl
```

Preview one random post without sending:

```bash
uv run hitz11 --db-path hitz11.db post --dry-run --skip-time-check
```

Run full daily flow (crawl + post) without sending:

```bash
uv run hitz11 --db-path hitz11.db daily --dry-run --skip-time-check
```

## 5) Testing

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check .
```

## 6) GitHub Actions 

The workflow stores state in a GitHub Release called `hitz11-state`.
It downloads `hitz11.db`, runs the daily command, then uploads the updated DB back as a release asset.
