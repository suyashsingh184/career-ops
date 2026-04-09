from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser

import httpx

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - exercised only in lean environments
    BeautifulSoup = None

from app.config import get_settings
from app.exceptions import SourceFetchError
from app.services.ingest.base import IngestedJob
from app.utils.retry import RATE_LIMITER, run_with_retry


def scrape_generic_jobs(url: str, company_name: str) -> list[IngestedJob]:
    settings = get_settings()

    def _fetch() -> httpx.Response:
        RATE_LIMITER.wait("scraper", settings.source_rate_limit_per_sec)
        response = httpx.get(
            url,
            timeout=settings.source_timeout_seconds,
            headers={"User-Agent": f"{settings.app_name} scraper"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SourceFetchError(str(exc)) from exc
        return response

    response = run_with_retry(_fetch, source_key=f"scraper:{company_name}")
    if BeautifulSoup is not None:
        soup = BeautifulSoup(response.text, "lxml")
        links = [(link.get_text(" ", strip=True), link.get("href", "")) for link in soup.select("a[href]")]
    else:
        class _LinkParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.links: list[tuple[str, str]] = []
                self._href = ""
                self._text: list[str] = []

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag == "a":
                    self._href = dict(attrs).get("href") or ""
                    self._text = []

            def handle_data(self, data: str) -> None:
                if self._href:
                    self._text.append(data)

            def handle_endtag(self, tag: str) -> None:
                if tag == "a" and self._href:
                    self.links.append((" ".join(self._text).strip(), self._href))
                    self._href = ""
                    self._text = []

        parser = _LinkParser()
        parser.feed(response.text)
        links = parser.links
    jobs: list[IngestedJob] = []
    for index, (title, href) in enumerate(links):
        if not title or len(title) < 4:
            continue
        lowered = title.lower()
        if "engineer" not in lowered and "developer" not in lowered and "platform" not in lowered:
            continue
        jobs.append(
            IngestedJob(
                source="scraper",
                external_id=f"{company_name}-{index}",
                company_name=company_name,
                title=title,
                location=None,
                employment_type=None,
                department=None,
                posted_at=datetime.utcnow(),
                url=href if href.startswith("http") else f"{url.rstrip('/')}/{href.lstrip('/')}",
                raw_description=title,
            )
        )
    return jobs
