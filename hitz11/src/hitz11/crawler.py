from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import httpx
from bs4 import BeautifulSoup


DEFAULT_BASE_URL = "https://josecanovas.com/diccionarioetimologico"
LETTER_PATHS = [f"{chr(c)}.html" for c in range(ord("a"), ord("z") + 1)]


@dataclass(slots=True)
class CrawledEntry:
    word: str
    definition: str
    etymology_text: str
    source_url: str


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_definition(full_text: str) -> str:
    quoted = re.search(r'"([^"]{8,240})"', full_text)
    if quoted:
        return quoted.group(1).strip()
    sentence = re.split(r"(?<=[.!?])\s", full_text, maxsplit=1)[0]
    return sentence[:240].strip()


def parse_letter_page(html: str, source_url: str) -> list[CrawledEntry]:
    soup = BeautifulSoup(html, "lxml")
    container = soup.find("div", id="contenido2020") or soup
    results: list[CrawledEntry] = []

    for dl in container.find_all("dl"):
        dt = dl.find("dt")
        dd = dl.find("dd")
        if not dt or not dd:
            continue
        word = _clean_text(dt.get_text(" ", strip=True))
        body = _clean_text(dd.get_text(" ", strip=True))
        if not word or not body:
            continue
        definition = _extract_definition(body)
        results.append(
            CrawledEntry(
                word=word,
                definition=definition,
                etymology_text=body,
                source_url=source_url,
            )
        )
    return results


def crawl_all_letters(
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = 30,
    paths: Iterable[str] = LETTER_PATHS,
) -> list[CrawledEntry]:
    found: list[CrawledEntry] = []
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        for path in paths:
            url = f"{base_url.rstrip('/')}/{path}"
            response = client.get(url)
            if response.status_code != 200:
                continue
            found.extend(parse_letter_page(response.text, url))
    return found
