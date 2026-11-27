"""Charts for Part 9."""

import matplotlib.pyplot as plt
import pandas as pd

from breathe_check.analysis import style
from breathe_check.standards import INDIA_DAILY_PM25, WHO_DAILY_PM25


def hour_label(h: int) -> str:
    if h == 0:
        return "midnight"
    if h == 12:
        return "noon"
    return f"{h % 12} {'am' if h < 12 else 'pm'}"


def plot_tomorrow(payload: dict):
    """Tomorrow's forecast for one city: middle line, low-high band, best window marked."""
    h = pd.DataFrame(payload["hours"]).sort_values("hour")
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.fill_between(h["hour"], h["low"], h["high"], color=style.SERIES[0], alpha=0.15, linewidth=0)
    ax.plot(h["hour"], h["mid"], color=style.SERIES[0])
    best = payload["best_window"]
    if best:
        ax.axvspan(best["start"], best["end"], color=style.SERIES[2], alpha=0.18, linewidth=0)
        ax.annotate(
            f"Best time: {hour_label(best['start'])} to {hour_label(best['end'])}\n"
            f"about {best['pm25']:.0f} µg/m³ ({best['category']})",
            (best["start"] + 1, h["mid"].max() * 0.98),
            ha="center",
            va="top",
            fontsize=9.5,
            color=style.TEXT,
        )
    style.limit_line(ax, INDIA_DAILY_PM25, "India daily limit (60)")
    style.limit_line(ax, WHO_DAILY_PM25, "WHO daily guideline (15)")
    ax.set_xticks(range(0, 24, 3), [hour_label(x) for x in range(0, 24, 3)])
    ax.set_xlim(0, 23)
    ax.set_ylim(0, max(h["high"].max() * 1.08, INDIA_DAILY_PM25 * 1.15))
    ax.set_ylabel("PM2.5 (µg/m³)")
    date = pd.Timestamp(payload["for_date"]).strftime("%A %d %B %Y")
    ax.set_title(f"{payload['name']}, {date}: when to go out", pad=22)
    style.subtitle(
        ax,
        "Line: middle forecast. Shaded: the range the real value should fall in 8 times out of 10.",
    )
    style.source_note(
        fig, "Forecast: Breathe Check, from Open-Meteo weather and CPCB readings via OpenAQ."
    )
    return fig


def plot_window_test(result: dict):
    """How often the chosen window really was among the day's cleanest, vs simple rules."""
    rows = [
        ("Forecast's best window", result["best_window_in_cleanest_third"]),
        ("Always 2 to 4 pm", result["always_2_to_4pm_in_cleanest_third"]),
        ("Any 2 hours, at random", 1 / 3),
    ]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    labels = [r[0] for r in rows][::-1]
    values = [r[1] for r in rows][::-1]
    colors = [style.SERIES[0] if lab.startswith("Forecast") else "#c3c2b7" for lab in labels]
    bars = ax.barh(labels, values, 0.6, color=colors, zorder=3)
    style.round_bars(bars)
    for bar, v in zip(bars, values, strict=True):
        ax.text(v + 0.01, bar.get_y() + bar.get_height() / 2, f"{v:.0%}", va="center", fontsize=10)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(axis="x", color=style.GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Share of days the 2 hours picked were among the cleanest third of the day")
    ax.set_title("The forecast picks a clean window more often than a fixed habit", pad=22)
    style.subtitle(
        ax,
        f"20 cities, June to November 2026: {result['days_tested']:,} city-days "
        "the models never saw.",
    )
    style.source_note(fig)
    return fig
