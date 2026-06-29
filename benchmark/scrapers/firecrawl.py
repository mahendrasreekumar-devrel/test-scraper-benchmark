from __future__ import annotations

import os
import requests
from .base import BaseScraper, ScrapeResult


class FirecrawlScraper(BaseScraper):
    name = "Firecrawl"
    BASE_URL = "https://api.firecrawl.dev/v1/scrape"

    def __init__(self):
        self.api_key = os.environ["FIRECRAWL_API_KEY"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        resp = requests.post(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown", "html"]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        markdown = data.get("markdown") or ""
        raw_html = data.get("html") or ""
        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=bool(markdown and len(markdown) > 100),
            response_time_ms=0,
            raw_bytes=len(raw_html.encode()),
            markdown_bytes=len(markdown.encode()),
            content_preview=markdown[:200],
        )
