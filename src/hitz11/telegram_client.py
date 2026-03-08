from __future__ import annotations

import httpx

from .models import Entry


MAX_MESSAGE_LEN = 4096


def compose_message(entry: Entry, post_type: str) -> str:
    prefix = "Recap del fin de semana" if post_type == "recap" else "Palabra del dia"
    body = (
        f"{prefix}: {entry.word.upper()}\n\n"
        f"Definicion: {entry.definition}\n\n"
        f"Etimologia:\n{entry.etymology_text}\n\n"
        f"Origen: {entry.origin_key}\n"
        f"Fuente: {entry.source_url}\n"
        "#Hitz11 #Etimologia"
    )
    if len(body) <= MAX_MESSAGE_LEN:
        return body
    reserved = len(body) - len(entry.etymology_text) + 20
    remaining = max(300, MAX_MESSAGE_LEN - reserved)
    truncated = entry.etymology_text[:remaining].rstrip() + "..."
    return (
        f"{prefix}: {entry.word}\n\n"
        f"Definicion: {entry.definition}\n\n"
        f"Etimologia:\n{truncated}\n\n"
        f"Origen: {entry.origin_key}\n"
        f"Fuente: {entry.source_url}\n"
        "#Hitz11 #Etimologia"
    )


def send_message(*, token: str, chat_id: str, text: str, timeout_seconds: int = 30) -> str:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    message_id = data["result"]["message_id"]
    return str(message_id)
