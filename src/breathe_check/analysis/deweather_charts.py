"""Charts for Part 6."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from breathe_check.analysis import style
from breathe_check.cities import get_city

FEATURE_NAMES = {
    "doy_sin": "Time of year",
    "doy_cos": "Time of year",
    "weekday": "Day of week",
    "temp_c": "Temperature",
    "temp_min_c": "Night-time low",
    "temp_max_c": "Daytime high",
    "humidity_pct": "Humidity",
    "dew_point_c": "Dew point",
    "rain_mm": "Rain",
    "pressure_hpa": "Air pressure",
    "cloud_pct": "Cloud",
    "wind_kmh": "Wind speed",
    "gust_max_kmh": "Strongest gust",
    "wind_u": "Wind east-west",
    "wind_v": "Wind north-south",
    "mixing_height_m": "Mixing height",
    "mixing_height_min_m": "Lowest mixing height",
    "sun_kwh_m2": "Sunshine",
    "wind_kmh_yesterday": "Wind speed yesterday",
    "mixing_height_m_yesterday": "Mixing height yesterday",
    "rain_mm_yesterday": "Rain yesterday",
    "temp_min_c_yesterday": "Night-time low yesterday",
    "humidity_pct_yesterday": "Humidity yesterday",
}


def plot_scores(scores: pd.DataFrame):
    """Dot plot: share of day-to-day variation explained, weather vs calendar only."""
    s = scores.sort_values("r2_weather")
    fig, ax = plt.subplots(figsize=(9, 6.4))
    y = np.arange(len(s))
    ax.hlines(y, s["r2_calendar_only"], s["r2_weather"], color=style.GRID, linewidth=3, zorder=1)
    ax.scatter(
        s["r2_calendar_only"],
        y,
        color=style.SERIES[1],
        s=46,
        zorder=3,
        edgecolor=style.SURFACE,
        linewidth=1.5,
        label="Time of year and weekday only",
    )
    ax.scatter(
        s["r2_weather"],
        y,
        color=style.SERIES[0],
        s=46,
        zorder=3,
        edgecolor=style.SURFACE,
        linewidth=1.5,
        label="Plus weather",
    )
    ax.set_yticks(y, [get_city(c).name for c in s["city"]])
    ax.set_xlim(-0.05, 1)
    ax.axvline(0, color=style.TEXT_MUTED, linewidth=0.8, zorder=0)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(axis="x", color=style.GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Share of day-to-day ups and downs the model gets right, on seasons it never saw")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title("Weather explains much more than the calendar alone", pad=22)
    style.subtitle(ax, "Each city's model tested one season at a time, trained on the others.")
    style.source_note(fig)
    return fig


def plot_importance(importance: pd.DataFrame, top: int = 10):
    # The two time-of-year inputs (sine and cosine of the day) are one idea: add them up
    named = importance.assign(feature=importance["feature"].map(lambda f: FEATURE_NAMES.get(f, f)))
    imp = (
        named.groupby("feature", as_index=False)["mean_abs_shap"]
        .sum()
        .sort_values("mean_abs_shap", ascending=False)
        .head(top)
        .iloc[::-1]
    )
    fig, ax = plt.subplots(figsize=(9, 4.8))
    labels = list(imp["feature"])
    bars = ax.barh(labels, imp["mean_abs_shap"] * 100, 0.62, color=style.SERIES[0], zorder=3)
    style.round_bars(bars)
    for bar, v in zip(bars, imp["mean_abs_shap"] * 100, strict=True):
        ax.text(
            bar.get_width() + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{v:.0f}%",
            va="center",
            fontsize=9.5,
            color=style.TEXT,
        )
    ax.grid(axis="x", color=style.GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Typical push on the day's predicted PM2.5 (about this many %)")
    ax.set_title("What drives Delhi's PM2.5 from day to day", pad=22)
    style.subtitle(
        ax,
        "Top 10 inputs to Delhi's model, by average SHAP value. "
        "'Time of year' also carries seasonal habits like crop burning.",
    )
    style.source_note(fig)
    return fig


def plot_actual_vs_expected(city: pd.DataFrame, season: str):
    s = city[city["season"] == season].copy()
    s["date"] = pd.to_datetime(s["date"])
    s = s[s["date"].dt.month.isin([10, 11, 12, 1, 2, 3])]
    # reindex to every day so missing days show as breaks, not straight lines
    s = s.set_index("date").asfreq("D").reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.plot(s["date"], s["pm25"], color=style.SERIES[0], linewidth=1.6)
    ax.plot(s["date"], s["expected"], color=style.SERIES[1], linewidth=1.6)
    last = s.dropna(subset=["pm25"]).iloc[-1]
    style.end_label(ax, last["date"], last["pm25"], "Actual", style.SERIES[0])
    style.end_label(
        ax, last["date"], last["expected"], "What the weather predicts", style.SERIES[1]
    )
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Delhi PM2.5 (µg/m³)")
    ax.set_title(
        f"Delhi, winter {season}: weather explains a lot, but not November to mid-December",
        pad=22,
    )
    style.subtitle(
        ax,
        "The gap between the lines is what weather can't explain: rules, fires, festivals, chance.",
    )
    style.source_note(fig)
    return fig
