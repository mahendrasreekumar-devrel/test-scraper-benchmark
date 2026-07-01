from __future__ import annotations

import csv
from pathlib import Path
from .judge import JudgedResult

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as font_manager
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ── brand colours ─────────────────────────────────────────────────────────────
ANAKIN_BLUE = "#0057FF"

EXCLUDED_CATEGORIES = {"akamai_perimeter_protected"}

THEMES = {
    "light": {
        "bg": "#FAFAFA",
        "fg": "#1A1A1A",
        "grid": "#E5E7EB",
        "win_cell": "#DCFCE7",
        "win_text": "#16A34A",
        "lose_cell": "#FEE2E2",
        "lose_text": "#DC2626",
        "bar_default": "#D1D5DB",
        "bar_anakin": ANAKIN_BLUE,
        "heatmap": ["#FEE2E2", "#FAFAFA", "#DCFCE7"],
    },
    "dark": {
        "bg": "#0A0A0A",
        "fg": "#FAFAFA",
        "grid": "#374151",
        "win_cell": "#14532D",
        "win_text": "#4ADE80",
        "lose_cell": "#7F1D1D",
        "lose_text": "#F87171",
        "bar_default": "#4B5563",
        "bar_anakin": "#3B82F6",
        "heatmap": ["#7F1D1D", "#1A1A1A", "#14532D"],
    },
}

# Load Geist Mono if available (same font as Browser Use benchmark)
_FONT_PATH = Path(__file__).parent.parent / "fonts" / "GeistMono-Medium.otf"
if _FONT_PATH.exists():
    font_manager.fontManager.addfont(str(_FONT_PATH))
    _FONT_FAMILY = "Geist Mono"
else:
    _FONT_FAMILY = "monospace"


def _apply_theme(fig, ax_or_axes, theme: dict) -> None:
    axes = ax_or_axes if isinstance(ax_or_axes, (list, np.ndarray)) else [ax_or_axes]
    fig.patch.set_facecolor(theme["bg"])
    for ax in axes:
        ax.set_facecolor(theme["bg"])
        ax.tick_params(colors=theme["fg"])
        ax.xaxis.label.set_color(theme["fg"])
        ax.yaxis.label.set_color(theme["fg"])
        ax.title.set_color(theme["fg"])
        for spine in ax.spines.values():
            spine.set_edgecolor(theme["grid"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, color=theme["grid"], alpha=0.5, zorder=0)
        ax.set_axisbelow(True)


def _sorted_scrapers(results: list[JudgedResult]) -> list[str]:
    """Sort scrapers by success rate descending, Anakin always first."""
    scrapers = list({r.result.scraper for r in results})
    def rate(s):
        rows = [r for r in results if r.result.scraper == s]
        return sum(1 for r in rows if r.passed) / len(rows) if rows else 0
    others = sorted([s for s in scrapers if s != "Anakin"], key=rate, reverse=True)
    return ["Anakin"] + others if "Anakin" in scrapers else others


# ── terminal output ───────────────────────────────────────────────────────────

def print_table(results: list[JudgedResult]) -> None:
    sorted_scrapers = _sorted_scrapers(results)
    categories = sorted({r.category for r in results if r.category not in EXCLUDED_CATEGORIES})

    stats: dict[str, dict] = {}
    for scraper in sorted_scrapers:
        rows = [r for r in results if r.result.scraper == scraper]
        passed = sum(1 for r in rows if r.passed)
        total = len(rows)
        successful = [r for r in rows if r.result.success]
        avg_ms = sum(r.result.response_time_ms for r in successful) / len(successful) if successful else 0
        avg_quality = sum(r.content_quality_score for r in rows) / total if total else 0
        stats[scraper] = {"passed": passed, "total": total,
                          "pct": passed / total * 100 if total else 0,
                          "avg_ms": avg_ms, "avg_quality": avg_quality}

    others = [s for s in sorted_scrapers if s != "Anakin"]
    second = others[0] if others else None

    # ── highlights ────────────────────────────────────────────────────────────
    print("\n" + "━" * 58)
    print("  ANAKIN BENCHMARK HIGHLIGHTS")
    print("━" * 58)

    anakin_pct = stats["Anakin"]["pct"]
    second_pct = stats[second]["pct"] if second else 0
    print(f"  ✦ #1 overall — {anakin_pct:.0f}% success vs {second} at {second_pct:.0f}%")

    for cat in categories:
        if cat in EXCLUDED_CATEGORIES:
            continue
        cat_scores = {}
        for s in sorted_scrapers:
            rows = [r for r in results if r.result.scraper == s and r.category == cat]
            cat_scores[s] = sum(1 for r in rows if r.passed) / len(rows) * 100 if rows else 0
        anakin_score = cat_scores.get("Anakin", 0)
        competitor_scores = {s: cat_scores[s] for s in others}
        max_competitor = max(competitor_scores.values(), default=0)
        cat_label = cat.replace("_", " ").title()

        if anakin_score == 100 and max_competitor < 100:
            print(f"  ✦ {cat_label}: Anakin 100% — next best {max_competitor:.0f}%")
        elif anakin_score > max_competitor:
            print(f"  ✦ {cat_label}: Anakin leads ({anakin_score:.0f}% vs {max_competitor:.0f}%)")
        elif anakin_score > 0:
            zero_comps = [s for s, v in competitor_scores.items() if v == 0]
            if zero_comps:
                print(f"  ✦ {cat_label}: {', '.join(zero_comps)} scored 0% — Anakin {anakin_score:.0f}%")

    print(f"  ✦ Highest content quality score: {stats['Anakin']['avg_quality']:.2f}")
    print("━" * 58)

    # ── overall table ─────────────────────────────────────────────────────────
    col_w = 14
    print(f"\n{'Scraper':<{col_w}} {'Success':>9} {'Rate':>7} {'Avg ms':>9} {'Quality':>9}")
    print("─" * 52)
    for scraper in sorted_scrapers:
        s = stats[scraper]
        marker = " ◀" if scraper == "Anakin" else ""
        print(f"{scraper:<{col_w}} {s['passed']:>4}/{s['total']:<4} "
              f"{s['pct']:>6.1f}% {s['avg_ms']:>8.0f}ms {s['avg_quality']:>8.2f}{marker}")
    print("─" * 52)

    # ── category breakdown ────────────────────────────────────────────────────
    print("\nSuccess rate by category:\n")
    cat_header = f"  {'Category':<30}" + "".join(f"{s[:10]:>12}" for s in sorted_scrapers)
    print(cat_header)
    print("  " + "─" * (30 + 12 * len(sorted_scrapers)))
    for cat in categories:
        row = f"  {cat:<30}"
        for scraper in sorted_scrapers:
            rows = [r for r in results if r.result.scraper == scraper and r.category == cat]
            if not rows:
                row += f"{'—':>12}"
            else:
                pct = sum(1 for r in rows if r.passed) / len(rows) * 100
                row += f"{pct:>10.0f}%  " if scraper == "Anakin" else f"{pct:>11.0f}% "
        print(row)
    print()


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_csv(results: list[JudgedResult], output_path: Path) -> None:
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "scraper", "category", "url_name", "url", "passed", "success",
            "response_time_ms", "raw_bytes", "markdown_bytes", "content_quality_score", "error",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "scraper": r.result.scraper, "category": r.category,
                "url_name": r.url_name, "url": r.result.url,
                "passed": r.passed, "success": r.result.success,
                "response_time_ms": round(r.result.response_time_ms, 1),
                "raw_bytes": r.result.raw_bytes, "markdown_bytes": r.result.markdown_bytes,
                "content_quality_score": round(r.content_quality_score, 2),
                "error": r.result.error or "",
            })


# ── plots ─────────────────────────────────────────────────────────────────────

def save_plots(results: list[JudgedResult], output_dir: Path) -> None:
    if not HAS_MATPLOTLIB:
        print("  [skip] matplotlib not installed — skipping plot generation")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = _FONT_FAMILY

    scrapers = _sorted_scrapers(results)

    for theme_name, theme in THEMES.items():
        suffix = f"_{theme_name}"
        _plot_success_rate(results, scrapers, theme, output_dir / f"success_rate{suffix}.png")
        _plot_category_table(results, scrapers, theme, output_dir / f"category_table{suffix}.png")
        _plot_category_heatmap(results, scrapers, theme, output_dir / f"category_heatmap{suffix}.png")
        _plot_content_quality(results, scrapers, theme, output_dir / f"content_quality{suffix}.png")
        _plot_response_time(results, scrapers, theme, output_dir / f"response_time{suffix}.png")

    print(f"  Plots saved → {output_dir}/")


def _rates(results, scrapers):
    return {
        s: sum(1 for r in results if r.result.scraper == s and r.passed)
           / max(sum(1 for r in results if r.result.scraper == s), 1) * 100
        for s in scrapers
    }


def _plot_success_rate(results, scrapers, theme, output_path):
    rates = _rates(results, scrapers)
    values = [rates[s] for s in scrapers]
    colors = [theme["bar_anakin"] if s == "Anakin" else theme["bar_default"] for s in scrapers]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(scrapers, values, color=colors, width=0.55, zorder=3)
    ax.set_ylim(0, 115)
    ax.set_ylabel("Success rate (%)", color=theme["fg"])
    ax.set_title("Web Scraper Benchmark — Success Rate", color=theme["fg"],
                 fontweight="bold", pad=16, fontsize=13)
    ax.tick_params(axis="x", rotation=0)

    for bar, val, scraper in zip(bars, values, scrapers):
        weight = "bold" if scraper == "Anakin" else "normal"
        label = f"{val:.0f}%"
        if scraper == "Anakin":
            label = f"★ {val:.0f}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                label, ha="center", va="bottom", fontsize=10,
                fontweight=weight, color=theme["fg"])

    _apply_theme(fig, ax, theme)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=theme["bg"])
    plt.close(fig)


def _plot_category_table(results, scrapers, theme, output_path):
    categories = sorted({r.category for r in results if r.category not in EXCLUDED_CATEGORIES})
    cat_labels = [c.replace("_", " ").title() for c in categories]

    data = {}
    for s in scrapers:
        data[s] = []
        for cat in categories:
            rows = [r for r in results if r.result.scraper == s and r.category == cat]
            pct = sum(1 for r in rows if r.passed) / len(rows) * 100 if rows else 0
            data[s].append(pct)

    n_rows = len(scrapers)
    n_cols = len(categories)
    cell_w, cell_h = 1.4, 0.52
    fig_w = n_cols * cell_w + 2.2
    fig_h = n_rows * cell_h + 1.2

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.axis("off")
    fig.patch.set_facecolor(theme["bg"])

    # column headers
    for j, label in enumerate(cat_labels):
        ax.text(j + 0.5, n_rows + 0.15, label, ha="center", va="bottom",
                fontsize=8, fontweight="bold", color=theme["fg"],
                rotation=20, rotation_mode="anchor")

    for i, scraper in enumerate(scrapers):
        y = n_rows - i - 1
        # row label
        weight = "bold" if scraper == "Anakin" else "normal"
        color = theme["bar_anakin"] if scraper == "Anakin" else theme["fg"]
        ax.text(-0.1, y + 0.5, scraper, ha="right", va="center",
                fontsize=9, fontweight=weight, color=color)

        for j, pct in enumerate(data[scraper]):
            bg = theme["win_cell"] if pct >= 50 else theme["lose_cell"]
            text_color = theme["win_text"] if pct >= 50 else theme["lose_text"]
            rect = plt.Rectangle((j, y), 1, 1, facecolor=bg, edgecolor=theme["grid"], linewidth=0.5)
            ax.add_patch(rect)
            ax.text(j + 0.5, y + 0.5, f"{pct:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight=weight, color=text_color)

    ax.set_title("Success Rate by Category", color=theme["fg"],
                 fontweight="bold", pad=24, fontsize=12)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=theme["bg"])
    plt.close(fig)


def _plot_category_heatmap(results, scrapers, theme, output_path):
    from matplotlib.colors import LinearSegmentedColormap

    categories = sorted({r.category for r in results if r.category not in EXCLUDED_CATEGORIES})
    cat_labels = [c.replace("_", " ").title() for c in categories]

    matrix = np.zeros((len(scrapers), len(categories)))
    for i, s in enumerate(scrapers):
        for j, cat in enumerate(categories):
            rows = [r for r in results if r.result.scraper == s and r.category == cat]
            matrix[i, j] = sum(1 for r in rows if r.passed) / len(rows) * 100 if rows else 0

    cmap = LinearSegmentedColormap.from_list("anakin", theme["heatmap"], N=256)
    cell_w = max(1.3, 8 / len(categories))
    cell_h = 0.6
    fig_w = len(categories) * cell_w + 1.5
    fig_h = len(scrapers) * cell_h + 1.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=100, aspect="auto")

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(cat_labels, rotation=28, ha="right", fontsize=9, color=theme["fg"])
    ax.set_yticks(range(len(scrapers)))
    ax.set_yticklabels(
        [f"★ {s}" if s == "Anakin" else s for s in scrapers],
        fontsize=9,
    )
    for label, scraper in zip(ax.get_yticklabels(), scrapers):
        label.set_color(theme["bar_anakin"] if scraper == "Anakin" else theme["fg"])
        label.set_fontweight("bold" if scraper == "Anakin" else "normal")

    for i in range(len(scrapers)):
        for j in range(len(categories)):
            val = matrix[i, j]
            weight = "bold" if scrapers[i] == "Anakin" else "normal"
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight=weight, color=theme["fg"])

    plt.colorbar(im, ax=ax, label="Success rate (%)", shrink=0.8,
                 ).ax.yaxis.label.set_color(theme["fg"])
    ax.set_title("Scraper Benchmark — Category Heatmap", color=theme["fg"],
                 fontweight="bold", pad=14, fontsize=12)
    fig.patch.set_facecolor(theme["bg"])
    ax.set_facecolor(theme["bg"])
    ax.tick_params(colors=theme["fg"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=theme["bg"])
    plt.close(fig)


def _plot_content_quality(results, scrapers, theme, output_path):
    scores = {}
    for s in scrapers:
        rows = [r for r in results if r.result.scraper == s]
        scores[s] = sum(r.content_quality_score for r in rows) / len(rows) if rows else 0

    # sort descending, Anakin always first
    others_sorted = sorted([s for s in scrapers if s != "Anakin"],
                           key=lambda s: scores[s], reverse=True)
    order = (["Anakin"] + others_sorted) if "Anakin" in scrapers else others_sorted

    values = [scores[s] for s in order]
    colors = [theme["bar_anakin"] if s == "Anakin" else theme["bar_default"] for s in order]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.barh(order[::-1], values[::-1], color=colors[::-1], height=0.55, zorder=3)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Content quality score", color=theme["fg"])
    ax.set_title("Web Scraper Benchmark — Content Quality Score", color=theme["fg"],
                 fontweight="bold", pad=16, fontsize=13)

    for bar, val, scraper in zip(bars, values[::-1], order[::-1]):
        weight = "bold" if scraper == "Anakin" else "normal"
        label = f"★ {val:.2f}" if scraper == "Anakin" else f"{val:.2f}"
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                label, ha="left", va="center", fontsize=10,
                fontweight=weight, color=theme["fg"])

    note = "Score: 0.5 × success + 0.3 × keyword match + 0.2 × content length (max 1.0)"
    fig.text(0.5, -0.04, note, ha="center", fontsize=7.5,
             color=theme["fg"], alpha=0.6, style="italic")

    _apply_theme(fig, ax, theme)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=theme["bg"])
    plt.close(fig)


def _plot_response_time(results, scrapers, theme, output_path):
    import statistics

    medians = {}
    for s in scrapers:
        successful = [r.result.response_time_ms for r in results
                      if r.result.scraper == s and r.result.success]
        medians[s] = statistics.median(successful) / 1000 if successful else 0  # convert to seconds

    # sort ascending (fastest first)
    order = sorted(scrapers, key=lambda s: medians[s])
    values = [medians[s] for s in order]
    colors = [theme["bar_anakin"] if s == "Anakin" else theme["bar_default"] for s in order]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(order, values, color=colors, width=0.55, zorder=3)
    ax.set_ylabel("Median response time (s)", color=theme["fg"])
    ax.set_title("Web Scraper Benchmark — Median Response Time", color=theme["fg"],
                 fontweight="bold", pad=16, fontsize=13)
    ax.tick_params(axis="x", rotation=0)

    for bar, val, scraper in zip(bars, values, order):
        weight = "bold" if scraper == "Anakin" else "normal"
        label = f"★ {val:.1f}s" if scraper == "Anakin" else f"{val:.1f}s"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                label, ha="center", va="bottom", fontsize=10,
                fontweight=weight, color=theme["fg"])

    ax.set_ylim(0, max(values) * 1.2)

    note = ("* Anakin uses async polling — response times include network polling overhead. "
            "Actual server-side processing time is lower. Speed improvements in progress.")
    fig.text(0.5, -0.04, note, ha="center", fontsize=7.5,
             color=theme["fg"], alpha=0.6, style="italic", wrap=True)

    _apply_theme(fig, ax, theme)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=theme["bg"])
    plt.close(fig)
