from __future__ import annotations

import os
import requests
from .base import BaseScraper, ScrapeResult


class OxylabsScraper(BaseScraper):
    name = "Oxylabs"
    BASE_URL = "https://realtime.oxylabs.io/v1/queries"

    def __init__(self):
        self.username = os.environ["OXYLABS_USERNAME"]
        self.password = os.environ["OXYLABS_PASSWORD"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        resp = requests.post(
            self.BASE_URL,
            auth=(self.username, self.password),
            json={
                "source": "universal",
                "url": url,
                "render": "html",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_html = data.get("results", [{}])[0].get("content") or ""
        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=bool(raw_html and len(raw_html) > 100),
            response_time_ms=0,
            raw_bytes=len(raw_html.encode()),
            markdown_bytes=0,  # Oxylabs returns raw HTML
            content_preview=raw_html[:200],
        )
