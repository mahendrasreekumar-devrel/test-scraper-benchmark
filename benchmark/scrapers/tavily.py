from __future__ import annotations

import os
import requests
from .base import BaseScraper, ScrapeResult


class TavilyScraper(BaseScraper):
    """
    Uses Tavily's /extract endpoint, which retrieves full page content from a URL.
    This is distinct from Tavily's search endpoint (which returns snippets only).
    """

    name = "Tavily"
    BASE_URL = "https://api.tavily.com/extract"

    def __init__(self):
        self.api_key = os.environ["TAVILY_API_KEY"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        resp = requests.post(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"urls": [url]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        raw_content = results[0].get("raw_content") or "" if results else ""
        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=bool(raw_content and len(raw_content) > 100),
            response_time_ms=0,
            raw_bytes=len(raw_content.encode()),
            markdown_bytes=0,  # Tavily /extract returns raw text, not structured markdown
            content_preview=raw_content[:200],
        )
