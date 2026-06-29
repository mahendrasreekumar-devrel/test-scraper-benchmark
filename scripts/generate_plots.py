#!/usr/bin/env python3
"""
Regenerate plots from an existing results JSON file.

Usage:
  python scripts/generate_plots.py results/results_2026-06-27_12-00-00.json
  python scripts/generate_plots.py results/official/2026-06-27.json --output results/official/plots
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.judge import JudgedResult
from benchmark.scrapers.base import ScrapeResult
from benchmark.report import save_plots, print_table


def load_results(path: Path) -> list[JudgedResult]:
    with open(path) as f:
        data = json.load(f)

    results = []
    for row in data["results"]:
        raw = ScrapeResult(
            scraper=row["scraper"],
            url=row["url"],
            success=row["success"],
            response_time_ms=row["response_time_ms"],
            raw_bytes=row["raw_bytes"],
            markdown_bytes=row["markdown_bytes"],
            error=row.get("error"),
            content_preview="",
        )
        judged = JudgedResult(
            result=raw,
            category=row["category"],
            url_name=row["url_name"],
            expected_content="",
            content_quality_score=row["content_quality_score"],
        )
        results.append(judged)
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark plots from a results JSON")
    parser.add_argument("results_file", help="Path to a results JSON file")
    parser.add_argument("--output", default=None,
                        help="Output directory for plots (default: same dir as results file)")
    args = parser.parse_args()

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"File not found: {results_path}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else results_path.parent / "plots"

    results = load_results(results_path)
    print(f"Loaded {len(results)} result rows from {results_path.name}")
    print_table(results)
    save_plots(results, output_dir)


if __name__ == "__main__":
    main()
