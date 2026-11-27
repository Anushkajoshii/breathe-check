"""Charts for Part 8."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from breathe_check.analysis import style
from breathe_check.cities import get_city
from breathe_check.standards import INDIA_ANNUAL_PM25, WHO_ANNUAL_PM25

MUTED_BAR = "#c3c2b7"
# light -> dark single-hue ramp, checked for visible steps (5 steps)
BAND_COLORS = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]
BANDS = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor or worse"]


def name(slug):
    return get_city(slug).name


def plot_yearly(summary: pd.DataFrame, season: str):
    s = summary[summary["season"] == season].sort_values("pm25")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [style.SERIES[0] if c == "indore" else MUTED_BAR for c in s["city"]]
    bars = ax.bar([name(c) for c in s["city"]], s["pm25"], 0.62, color=colors, zorder=3)
    style.round_bars(bars)
    for bar, v in zip(bars, s["pm25"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 2,
            f"{v:.0f}",
            ha="center",
            fontsize=10,
            color=style.TEXT,
        )
    style.limit_line(ax, INDIA_ANNUAL_PM25, "India yearly limit (40)")
    style.limit_line(ax, WHO_ANNUAL_PM25, "WHO yearly guideline (5)")
    style.cigarette_scale(ax)
    ax.set_ylim(0, s["pm25"].max() * 1.12)
    ax.set_ylabel("Average PM2.5 (µg/m³)")
    ax.grid(axis="x", visible=False)
    ax.set_title("Indore is the cleanest of its neighbours, and right at India's limit", pad=22)
    style.subtitle(
        ax,
        f"Average PM2.5, July {season[:4]} to June 20{season[-2:]}. "
        "WHO's guideline is 8 times lower.",
    )
    style.source_note(fig)
    return fig


def plot_bands(bands: pd.DataFrame, order: list[str]):
    b = bands.copy()
    b["Very Poor or worse"] = b["Very Poor"] + b["Severe"]
    b = b.set_index("city").loc[order[::-1], BANDS]
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    left = np.zeros(len(b))
    y = np.arange(len(b))
    for color, band in zip(BAND_COLORS, BANDS, strict=True):
        vals = b[band].values
        ax.barh(
            y,
            vals,
            left=left,
            color=color,
            height=0.62,
            edgecolor=style.SURFACE,
            linewidth=2,
            label=band,
            zorder=3,
        )
        for yi, (start, v) in enumerate(zip(left, vals, strict=True)):
            if v >= 0.08:
                ink = style.TEXT if color == BAND_COLORS[0] else "#ffffff"
                ax.text(
                    start + v / 2, yi, f"{v:.0%}", ha="center", va="center", fontsize=9, color=ink
                )
        left += vals
    ax.set_yticks(y, [name(c) for c in b.index])
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(visible=False)
    ax.legend(ncol=5, loc="upper left", bbox_to_anchor=(0, -0.1), fontsize=9, handlelength=1.2)
    ax.set_title("Most of Indore's days are 'Good' or 'Satisfactory' on India's scale", pad=22)
    style.subtitle(
        ax, "Share of days in each India AQI category (PM2.5 only), July 2025 to June 2026."
    )
    style.source_note(
        fig, "Data: CPCB via OpenAQ. Categories: CPCB National AQI. Breathe Check.", y=-0.08
    )
    return fig


def plot_weather_fair(wf: pd.DataFrame):
    w = wf.sort_values("vs_weather_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 6.4))
    y = np.arange(len(w))
    for yi, (city, v) in enumerate(zip(w["city"], w["vs_weather_pct"], strict=True)):
        color = style.SERIES[0] if city == "indore" else MUTED_BAR
        ax.hlines(yi, 0, v, color=color, linewidth=2.5, zorder=2)
        ax.plot(
            v,
            yi,
            "o",
            color=color,
            markersize=8,
            markeredgecolor=style.SURFACE,
            markeredgewidth=1.5,
            zorder=3,
        )
        ax.annotate(
            f"{v:+.0f}%",
            (v, yi),
            xytext=(8 if v >= 0 else -8, 0),
            textcoords="offset points",
            ha="left" if v >= 0 else "right",
            va="center",
            fontsize=8.5,
            color=style.TEXT_SECONDARY,
        )
    ax.axvline(0, color=style.TEXT_MUTED, linewidth=1)
    ax.set_yticks(y, [name(c) for c in w["city"]])
    ax.grid(axis="x", color=style.GRID)
    ax.grid(axis="y", visible=False)
    lim = max(abs(w["vs_weather_pct"]).max() * 1.25, 10)
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Typical day vs what its weather predicts (%). Left = cleaner than its weather.")
    ax.set_title("Judged against its weather, Indore is ordinary", pad=22)
    style.subtitle(ax, "One shared weather model for all 20 cities, July 2025 to June 2026.")
    style.source_note(fig)
    return fig
