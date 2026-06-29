from __future__ import annotations

import os
import requests
from .base import BaseScraper, ScrapeResult


class ZenRowsScraper(BaseScraper):
    name = "ZenRows"
    BASE_URL = "https://api.zenrows.com/v1/"

    def __init__(self):
        self.api_key = os.environ["ZENROWS_API_KEY"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        resp = requests.get(
            self.BASE_URL,
            params={
                "apikey": self.api_key,
                "url": url,
                "js_render": "true",
                "premium_proxy": "true",
                "markdown_response": "true",
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.text or ""
        raw_bytes = len(content.encode())
        # ZenRows returns markdown when markdown_response=true
        is_markdown = "markdown_response" in resp.request.url
        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=bool(content and len(content) > 100),
            response_time_ms=0,
            raw_bytes=raw_bytes,
            markdown_bytes=raw_bytes if is_markdown else 0,
            content_preview=content[:200],
        )
