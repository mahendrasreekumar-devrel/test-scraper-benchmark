#!/usr/bin/env python3
"""
scraper-benchmark — CLI entry point

Usage:
  python run_benchmark.py                          # run all configured scrapers
  python run_benchmark.py --scrapers anakin firecrawl
  python run_benchmark.py --concurrency 4
  python run_benchmark.py --no-plots
  python run_benchmark.py --results-dir my_results
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from benchmark.runner import run_benchmark, load_urls, save_results
from benchmark.report import print_table, save_csv, save_plots
from benchmark.scrapers import ALL_SCRAPERS

SCRAPER_NAMES = {cls.__name__.replace("Scraper", "").lower(): cls for cls in ALL_SCRAPERS}
SCRAPER_NAMES["anakin"] = next(c for c in ALL_SCRAPERS if c.__name__ == "AnakinScraper")


def main():
    parser = argparse.ArgumentParser(description="Scraper Benchmark")
    parser.add_argument(
        "--scrapers", nargs="+",
        help=f"Which scrapers to run. Options: {', '.join(SCRAPER_NAMES)}. Default: all configured.",
    )
    parser.add_argument("--concurrency", type=int, default=6,
                        help="Max parallel requests (default: 6)")
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip PNG chart generation")
    parser.add_argument("--results-dir", default="results",
                        help="Directory to write results JSON and CSV (default: results/)")
    args = parser.parse_args()

    # ── resolve scrapers ─────────────────────────────────────────────────────
    if args.scrapers:
        selected_classes = []
        for name in args.scrapers:
            cls = SCRAPER_NAMES.get(name.lower())
            if not cls:
                print(f"Unknown scraper: {name}. Options: {', '.join(SCRAPER_NAMES)}")
                sys.exit(1)
            selected_classes.append(cls)
    else:
        selected_classes = None  # runner picks up all that have keys set

    # ── load URLs ─────────────────────────────────────────────────────────────
    urls = load_urls()
    print(f"\nLoaded {len(urls)} URLs across categories.")
    print(f"Running with concurrency={args.concurrency} ...\n")

    # ── run ───────────────────────────────────────────────────────────────────
    scrapers = None
    if selected_classes:
        from benchmark.runner import _init_scrapers
        # filter to selected
        all_active = _init_scrapers()
        scrapers = [s for s in all_active if type(s) in selected_classes]

    results = run_benchmark(scrapers=scrapers, concurrency=args.concurrency, urls=urls)

    if not results:
        print("No results collected. Check your API keys in .env")
        sys.exit(1)

    # ── report ────────────────────────────────────────────────────────────────
    print_table(results)

    results_dir = Path(args.results_dir)
    json_path = save_results(results, results_dir)
    print(f"  Results JSON → {json_path}")

    csv_path = results_dir / (json_path.stem + ".csv")
    save_csv(results, csv_path)
    print(f"  Results CSV  → {csv_path}")

    if not args.no_plots:
        plots_dir = results_dir / "plots"
        save_plots(results, plots_dir)


if __name__ == "__main__":
    main()
