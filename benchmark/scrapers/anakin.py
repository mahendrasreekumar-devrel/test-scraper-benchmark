from __future__ import annotations

import os
import time
import requests
from .base import BaseScraper, ScrapeResult

POLL_INTERVAL = 1.5  # seconds between status checks
MAX_POLLS = 20


class AnakinScraper(BaseScraper):
    name = "Anakin"
    BASE_URL = "https://api.anakin.io/v1/url-scraper"

    def __init__(self):
        self.api_key = os.environ["ANAKIN_API_KEY"]

    def scrape(self, url: str) -> ScrapeResult:
        return self._timed_scrape(url, self._do_scrape)

    def _do_scrape(self, url: str) -> ScrapeResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Submit job
        resp = requests.post(self.BASE_URL, headers=headers, json={"url": url}, timeout=30)
        resp.raise_for_status()
        job_id = resp.json()["jobId"]

        # Poll until complete
        for _ in range(MAX_POLLS):
            time.sleep(POLL_INTERVAL)
            poll = requests.get(f"{self.BASE_URL}/{job_id}", headers=headers, timeout=30)
            poll.raise_for_status()
            data = poll.json()
            if data["status"] == "completed":
                markdown = data.get("markdown") or ""
                raw_html = data.get("html") or ""
                return ScrapeResult(
                    scraper=self.name,
                    url=url,
                    success=bool(markdown and len(markdown) > 100),
                    response_time_ms=data.get("durationMs", 0),
                    raw_bytes=len(raw_html.encode()),
                    markdown_bytes=len(markdown.encode()),
                    content_preview=markdown[:200],
                )
            if data["status"] == "failed":
                return ScrapeResult(
                    scraper=self.name,
                    url=url,
                    success=False,
                    response_time_ms=0,
                    error=data.get("error", "job failed"),
                )

        return ScrapeResult(
            scraper=self.name,
            url=url,
            success=False,
            response_time_ms=0,
            error="polling timeout",
        )
