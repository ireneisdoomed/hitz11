from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    telegram_bot_token: str = Field(min_length=10)
    telegram_chat_id: str = Field(min_length=2)
    timezone: str = "Europe/Madrid"
    origin_key: str = "basque"
    language: str = "es"
    recency_days: int = 30


def load_settings(require_telegram: bool = True) -> Settings:
    load_dotenv()
    payload = {
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "timezone": os.getenv("TIMEZONE", "Europe/Madrid"),
        "origin_key": os.getenv("ORIGIN_KEY", "basque"),
        "language": os.getenv("LANGUAGE", "es"),
        "recency_days": int(os.getenv("RECENCY_DAYS", "30")),
    }

    if not require_telegram:
        payload["telegram_bot_token"] = payload["telegram_bot_token"] or "dummy-token"
        payload["telegram_chat_id"] = payload["telegram_chat_id"] or "dummy-chat"

    try:
        return Settings(**payload)
    except ValidationError as exc:
        raise SystemExit(f"Invalid settings: {exc}") from exc
