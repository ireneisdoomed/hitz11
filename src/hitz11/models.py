from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Entry:
    id: int
    word: str
    definition: str
    etymology_text: str
    origin_key: str
    language: str
    source_url: str
