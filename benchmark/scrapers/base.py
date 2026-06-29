from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScrapeResult:
    scraper: str
    url: str
    success: bool
    response_time_ms: float
    raw_bytes: int = 0
    markdown_bytes: int = 0
    error: Optional[str] = None
    content_preview: str = ""


class BaseScraper(ABC):
    name: str

    @abstractmethod
    def scrape(self, url: str) -> ScrapeResult:
        ...

    def _timed_scrape(self, url: str, fn) -> ScrapeResult:
        start = time.perf_counter()
        try:
            result = fn(url)
            result.response_time_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as exc:
            return ScrapeResult(
                scraper=self.name,
                url=url,
                success=False,
                response_time_ms=(time.perf_counter() - start) * 1000,
                error=str(exc),
            )
