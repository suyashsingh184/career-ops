from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser
from difflib import SequenceMatcher
from typing import Optional

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - exercised only in lean environments
    BeautifulSoup = None

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+\-/#.]{1,}")
STOPWORDS = {
    "with",
    "from",
    "that",
    "this",
    "have",
    "will",
    "your",
    "team",
    "years",
    "experience",
    "work",
    "using",
    "build",
    "role",
    "you",
    "for",
    "and",
    "the",
}

BOILERPLATE_PATTERNS = [
    re.compile(r"we are an equal opportunity employer.*", re.IGNORECASE),
    re.compile(r"reasonable accommodations? .*", re.IGNORECASE),
    re.compile(r"pursuant to .* law.*", re.IGNORECASE),
    re.compile(r"compensation range.*", re.IGNORECASE),
]


def strip_html(value: str) -> str:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(value or "", "lxml")
        return soup.get_text(" ", strip=True)

    class _HTMLStripper(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self.parts.append(data)

    parser = _HTMLStripper()
    parser.feed(value or "")
    return " ".join(parser.parts)


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_description(raw_description: str) -> str:
    normalized = collapse_whitespace(strip_html(raw_description))
    for pattern in BOILERPLATE_PATTERNS:
        normalized = pattern.sub("", normalized)
    return collapse_whitespace(normalized)


def normalize_company_name(value: str) -> str:
    normalized = collapse_whitespace(value).lower()
    normalized = re.sub(r"\b(inc|llc|ltd|corp|corporation|company)\b\.?", "", normalized)
    normalized = re.sub(r"[,.;:]+", " ", normalized)
    return collapse_whitespace(normalized)


def normalize_location(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = collapse_whitespace(value).lower().replace("remote-friendly", "remote")
    normalized = normalized.replace("united states", "us")
    return normalized


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def keyword_candidates(text: str) -> list[str]:
    return [match.group(0).lower() for match in WORD_RE.finditer(text) if match.group(0).lower() not in STOPWORDS]


def most_common_keywords(text: str, limit: int = 15) -> list[str]:
    counts = Counter(keyword_candidates(text))
    return [word for word, _ in counts.most_common(limit)]
