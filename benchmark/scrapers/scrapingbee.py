from __future__ import annotations

import os
import requests
from .base import BaseScraper, ScrapeResult


class ScrapingBeeScraper(BaseScraper):
    name = "ScrapingBee"
    BASE_URL = "https://app.scrapingbee.com/api/v1/"

    def __init__(self):
        self.api_key = os.environ["SCRAPINGBEE_API_KEY"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        resp = requests.get(
            self.BASE_URL,
            params={
                "api_key": self.api_key,
                "url": url,
                "render_js": "true",
                "premium_proxy": "true",
            },
            timeout=60,
        )
        resp.raise_for_status()
        raw_html = resp.text or ""
        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=bool(raw_html and len(raw_html) > 100),
            response_time_ms=0,
            raw_bytes=len(raw_html.encode()),
            markdown_bytes=0,  # ScrapingBee returns raw HTML
            content_preview=raw_html[:200],
        )
