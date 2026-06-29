from __future__ import annotations

from dataclasses import dataclass
from .scrapers.base import ScrapeResult


@dataclass
class JudgedResult:
    result: ScrapeResult
    category: str
    url_name: str
    expected_content: str
    content_quality_score: float  # 0.0 – 1.0

    @property
    def passed(self) -> bool:
        return self.result.success and self.content_quality_score >= 0.5


def judge(result: ScrapeResult, expected_content: str, category: str, url_name: str) -> JudgedResult:
    """
    Score a scrape result against simple quality signals:
    - Did we get a response at all? (binary)
    - Does the content contain the expected string? (weighted)
    - Is there enough content to be real? (word count proxy)

    Score breakdown:
      0.5 — success flag is True and raw bytes > 500
      0.3 — expected_content found in the response (case-insensitive)
      0.2 — content is >1000 bytes (non-trivial page returned)
    """
    if not result.success or not result.content_preview:
        return JudgedResult(
            result=result,
            category=category,
            url_name=url_name,
            expected_content=expected_content,
            content_quality_score=0.0,
        )

    score = 0.0
    preview_lower = result.content_preview.lower()
    content_size = result.raw_bytes or result.markdown_bytes

    if result.success and content_size > 500:
        score += 0.5
    if expected_content.lower() in preview_lower:
        score += 0.3
    if content_size > 1000:
        score += 0.2

    return JudgedResult(
        result=result,
        category=category,
        url_name=url_name,
        expected_content=expected_content,
        content_quality_score=min(score, 1.0),
    )
