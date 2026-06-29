from __future__ import annotations

import os
import yaml
import json
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from .scrapers import ALL_SCRAPERS
from .scrapers.base import BaseScraper
from .judge import JudgedResult, judge


URLS_FILE = Path(__file__).parent.parent / "urls" / "test_urls.yaml"


def load_urls() -> list[dict]:
    with open(URLS_FILE) as f:
        data = yaml.safe_load(f)
    entries = []
    for category, cat_data in data["categories"].items():
        for item in cat_data["urls"]:
            entries.append({
                "category": category,
                "name": item["name"],
                "url": item["url"],
                "expected_content": item["expected_content"],
            })
    return entries


def _run_one(scraper: BaseScraper, entry: dict) -> JudgedResult:
    raw = scraper.scrape(entry["url"])
    return judge(raw, entry["expected_content"], entry["category"], entry["name"])


def run_benchmark(
    scrapers: list = None,
    concurrency: int = 6,
    urls: list[dict] = None,
) -> list[JudgedResult]:
    if scrapers is None:
        scrapers = _init_scrapers()
    if urls is None:
        urls = load_urls()

    tasks = [(scraper, entry) for scraper in scrapers for entry in urls]
    results: list[JudgedResult] = []

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_run_one, s, e): (s.name, e["name"]) for s, e in tasks}
        for future in as_completed(futures):
            scraper_name, url_name = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f"  [error] {scraper_name} / {url_name}: {exc}")

    return results


def _init_scrapers() -> list[BaseScraper]:
    active = []
    env_map = {
        "AnakinScraper": "ANAKIN_API_KEY",
        "FirecrawlScraper": "FIRECRAWL_API_KEY",
        "ZenRowsScraper": "ZENROWS_API_KEY",
        "ScraperAPIScraper": "SCRAPERAPI_KEY",
        "OxylabsScraper": "OXYLABS_USERNAME",
        "ScrapingBeeScraper": "SCRAPINGBEE_API_KEY",
        "TavilyScraper": "TAVILY_API_KEY",
    }
    for cls in ALL_SCRAPERS:
        required_env = env_map.get(cls.__name__)
        if required_env and not os.environ.get(required_env):
            print(f"  [skip] {cls.__name__} — {required_env} not set")
            continue
        try:
            active.append(cls())
        except Exception as exc:
            print(f"  [skip] {cls.__name__} — {exc}")
    return active


def save_results(results: list[JudgedResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"results_{timestamp}.json"

    serialisable = []
    for r in results:
        serialisable.append({
            "scraper": r.result.scraper,
            "url": r.result.url,
            "url_name": r.url_name,
            "category": r.category,
            "success": r.result.success,
            "passed": r.passed,
            "response_time_ms": round(r.result.response_time_ms, 1),
            "raw_bytes": r.result.raw_bytes,
            "markdown_bytes": r.result.markdown_bytes,
            "content_quality_score": round(r.content_quality_score, 2),
            "error": r.result.error,
        })

    with open(output_path, "w") as f:
        json.dump({"timestamp": timestamp, "results": serialisable}, f, indent=2)

    return output_path
