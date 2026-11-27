"""Part 5: a first look at the data. Each function returns a small table;
the matching plot_ function draws it. Kept separate so the numbers are testable."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from breathe_check.analysis import style
from breathe_check.cities import get_city
from breathe_check.standards import INDIA_DAILY_PM25, WHO_DAILY_PM25

GROUPS = {
    "grap": "Delhi-NCR",
    "indore": "Indore and peers",
    "indore_peer": "Indore and peers",
    "control": "Other cities",
    "other": "Other cities",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WINTER = (11, 12, 1, 2)


def name(slug: str) -> str:
    return get_city(slug).name


# ---------- 1. How many stations report, over time ----------


def station_coverage(city_day: pd.DataFrame) -> pd.DataFrame:
    """Average number of usable stations per day, by month and city group."""
    df = city_day.assign(group=city_day["city_role"].map(GROUPS))
    daily = df.groupby(["group", "date"], as_index=False)["n_stations"].sum()
    daily["month"] = pd.to_datetime(daily["date"]).dt.to_period("M").dt.to_timestamp()
    monthly = daily.groupby(["group", "month"], as_index=False)["n_stations"].mean()
    # fill months with no data at all as zero, so the gap shows
    months = pd.date_range(monthly["month"].min(), monthly["month"].max(), freq="MS")
    full = pd.MultiIndex.from_product([monthly["group"].unique(), months], names=["group", "month"])
    return monthly.set_index(["group", "month"]).reindex(full, fill_value=0).reset_index()


def plot_station_coverage(table: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    order = ["Delhi-NCR", "Other cities", "Indore and peers"]
    for color, group in zip(style.SERIES, order, strict=True):
        part = table[table["group"] == group]
        ax.plot(part["month"], part["n_stations"], color=color)
        last = part.iloc[-1]
        style.end_label(ax, last["month"], last["n_stations"], group, color)
    gap_start, gap_end = pd.Timestamp("2022-11-01"), pd.Timestamp("2025-02-01")
    ax.axvspan(gap_start, gap_end, color=style.GRID, alpha=0.6, linewidth=0)
    ax.text(
        gap_start + (gap_end - gap_start) / 2,
        ax.get_ylim()[1] * 0.92,
        "No CPCB data on OpenAQ",
        ha="center",
        color=style.TEXT_SECONDARY,
        fontsize=9,
    )
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Usable stations per day")
    ax.set_title("A three-year hole in the record", pad=22)
    style.subtitle(ax, "Stations with a usable daily reading, averaged by month.")
    style.source_note(fig)
    return fig


# ---------- 2. The yearly cycle ----------


def monthly_profile(city_day: pd.DataFrame, cities: list[str]) -> pd.DataFrame:
    df = city_day[city_day["city"].isin(cities) & city_day["pm25"].notna()]
    return df.groupby(["city", "month"], as_index=False).agg(
        pm25=("pm25", "mean"), days=("pm25", "size")
    )


def plot_monthly_profile(table: pd.DataFrame, cities: list[str]):
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for color, city in zip(style.SERIES, cities, strict=True):
        part = table[table["city"] == city].sort_values("month")
        ax.plot(part["month"], part["pm25"], color=color)
        style.end_label(ax, 12, part["pm25"].iloc[-1], name(city), color)
    ax.set_xticks(range(1, 13), MONTHS)
    ax.set_xlim(0.7, 12.3)
    ax.set_ylim(bottom=0)
    style.limit_line(ax, INDIA_DAILY_PM25, "India daily limit (60)")
    style.limit_line(ax, WHO_DAILY_PM25, "WHO daily guideline (15)")
    ax.set_ylabel("PM2.5 (µg/m³), average day")
    ax.set_title("Winter is the problem everywhere, but most in Delhi", pad=22)
    style.subtitle(ax, "Average daily PM2.5 by month, all years with data (2018-2022, 2025-2026).")
    style.source_note(fig)
    return fig


# ---------- 3. Hour of the day ----------


def hourly_profile(city_hour: pd.DataFrame, cities: list[str]) -> pd.DataFrame:
    df = city_hour[city_hour["city"].isin(cities)].copy()
    df["season"] = np.where(
        pd.to_datetime(df["time_ist"]).dt.month.isin(WINTER), "Winter (Nov-Feb)", "Rest of year"
    )
    return df.groupby(["season", "city", "hour"], as_index=False)["pm25"].mean()


def plot_hourly_profile(table: pd.DataFrame, cities: list[str]):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, season in zip(axes, ["Winter (Nov-Feb)", "Rest of year"], strict=True):
        for color, city in zip(style.SERIES, cities, strict=True):
            part = table[(table["season"] == season) & (table["city"] == city)].sort_values("hour")
            ax.plot(part["hour"], part["pm25"], color=color)
            style.end_label(ax, 23, part["pm25"].iloc[-1], name(city), color)
        ax.set_xticks([0, 6, 12, 18, 23], ["midnight", "6 am", "noon", "6 pm", "11 pm"])
        ax.set_xlim(0, 23)
        ax.set_ylim(bottom=0)
        ax.set_title(season, fontsize=11, pad=6)
        ax.axvspan(13, 17, color=style.GRID, alpha=0.5, linewidth=0)
    axes[0].set_ylabel("PM2.5 (µg/m³), average hour")
    axes[1].text(
        15,
        axes[1].get_ylim()[1] * 0.95,
        "cleanest",
        ha="center",
        color=style.TEXT_SECONDARY,
        fontsize=9,
    )
    fig.suptitle(
        "Afternoons are cleanest; late nights and early mornings are worst",
        x=0.01,
        ha="left",
        fontsize=13,
        fontweight="bold",
        y=1.04,
    )
    fig.text(
        0.01,
        0.97,
        "Average PM2.5 by hour of day, Feb 2025 to Nov 2026. "
        "The sun mixes the air upward after noon.",
        color=style.TEXT_SECONDARY,
        fontsize=10,
    )
    style.source_note(fig)
    fig.tight_layout()
    return fig


# ---------- 4. Diwali ----------


def diwali_window(city_day: pd.DataFrame, cities: list[str], days: int = 10) -> pd.DataFrame:
    df = city_day[
        city_day["city"].isin(cities)
        & city_day["days_from_diwali"].between(-days, days)
        & city_day["pm25"].notna()
    ]
    return df.groupby(["city", "days_from_diwali"], as_index=False).agg(
        pm25=("pm25", "mean"), years=("year", "nunique")
    )


def diwali_jump(window: pd.DataFrame) -> pd.DataFrame:
    """Day after Diwali vs the average of days -10 to -4 (the week before the run-up)."""
    rows = []
    for city, part in window.groupby("city"):
        before = part[part["days_from_diwali"].between(-10, -4)]["pm25"].mean()
        after = part.loc[part["days_from_diwali"] == 1, "pm25"].mean()
        rows.append(
            {"city": city, "week_before": before, "day_after": after, "ratio": after / before}
        )
    return pd.DataFrame(rows)


def plot_diwali(window: pd.DataFrame, cities: list[str]):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for color, city in zip(style.SERIES, cities, strict=True):
        part = window[window["city"] == city].sort_values("days_from_diwali")
        ax.plot(part["days_from_diwali"], part["pm25"], color=color)
        style.end_label(
            ax, part["days_from_diwali"].iloc[-1], part["pm25"].iloc[-1], name(city), color
        )
    ax.axvline(0, color=style.TEXT_MUTED, linewidth=1, zorder=1)
    ax.text(
        -0.25,
        ax.get_ylim()[1] * 0.97,
        "Diwali",
        color=style.TEXT_SECONDARY,
        fontsize=9,
        va="top",
        ha="right",
    )
    ax.set_xlim(-10, 10)
    ax.set_xticks(range(-10, 11, 2))
    ax.set_ylim(bottom=0)
    style.limit_line(ax, INDIA_DAILY_PM25, "India daily limit (60)")
    ax.set_xlabel("Days from Diwali")
    ax.set_ylabel("PM2.5 (µg/m³), average day")
    ax.set_title("The day after Diwali is the dirtiest day of the window", pad=22)
    years = int(window["years"].max())
    style.subtitle(ax, f"Daily PM2.5 around Diwali, averaged over the {years} years with data.")
    style.source_note(fig)
    return fig


# ---------- 5. Crop fires and wind ----------

FIRE_BINS = [-1, 100, 500, 1500, np.inf]
FIRE_LABELS = ["Under 100", "100-500", "500-1,500", "Over 1,500"]


def fires_and_wind(city_day: pd.DataFrame, city: str = "delhi") -> pd.DataFrame:
    """Delhi PM2.5 in the burning season by yesterday's fire count and wind direction."""
    df = city_day[
        (city_day["city"] == city)
        & city_day["pm25"].notna()
        & (
            ((city_day["month"] == 10) & (pd.to_datetime(city_day["date"]).dt.day >= 15))
            | (city_day["month"] == 11)
        )
    ].copy()
    df["fires_bin"] = pd.cut(df["fires_confident_yesterday"], FIRE_BINS, labels=FIRE_LABELS)
    # Punjab and Haryana lie north-west of Delhi
    df["wind"] = np.where(
        df["wind_from_deg"].between(270, 360), "Wind from the north-west", "Other winds"
    )
    return df.groupby(["wind", "fires_bin"], observed=False, as_index=False).agg(
        pm25=("pm25", "mean"), days=("pm25", "size")
    )


def plot_fires_and_wind(table: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.4))
    winds = ["Wind from the north-west", "Other winds"]
    x = np.arange(len(FIRE_LABELS))
    width = 0.38
    for i, (color, wind) in enumerate(zip(style.SERIES, winds, strict=False)):
        part = table[table["wind"] == wind].set_index("fires_bin").reindex(FIRE_LABELS)
        bars = ax.bar(
            x + (i - 0.5) * (width + 0.02), part["pm25"], width, color=color, label=wind, zorder=3
        )
        for bar, days in zip(bars, part["days"], strict=True):
            if days and not np.isnan(bar.get_height()):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 3,
                    f"{days} d",
                    ha="center",
                    fontsize=8,
                    color=style.TEXT_MUTED,
                )
    ax.set_xticks(x, FIRE_LABELS)
    ax.set_xlabel("Crop fires seen in Punjab and Haryana the day before")
    ax.set_ylabel("Delhi PM2.5 (µg/m³), average day")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title("Delhi's worst smoke-season days follow the biggest fire days", pad=22)
    style.subtitle(
        ax,
        "Delhi, 15 Oct to 30 Nov. Below 1,500 fires there's little difference. "
        "Not yet weather-adjusted.",
    )
    style.source_note(fig)
    return fig


# ---------- 6. Weather: mixing height ----------


def mixing_height_effect(
    city_day: pd.DataFrame, city: str = "delhi", bins: int = 6
) -> pd.DataFrame:
    df = city_day[
        (city_day["city"] == city) & city_day["month"].isin(WINTER) & city_day["pm25"].notna()
    ].copy()
    df["bin"] = pd.qcut(df["mixing_height_m"], bins)
    out = df.groupby("bin", observed=True, as_index=False).agg(
        mixing_m=("mixing_height_m", "median"), pm25=("pm25", "mean"), days=("pm25", "size")
    )
    return out.drop(columns="bin")


def plot_mixing_height(table: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    labels = [f"~{int(round(m, -1))} m" for m in table["mixing_m"]]
    bars = ax.bar(range(len(table)), table["pm25"], 0.62, color=style.SERIES[0], zorder=3)
    for bar, value in zip(bars, table["pm25"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 4,
            f"{value:.0f}",
            ha="center",
            fontsize=9,
            color=style.TEXT,
        )
    ax.set_xticks(range(len(table)), labels)
    ax.set_xlabel(
        "Mixing height: how high the air can rise and spread (daily average, lowest to highest)"
    )
    ax.set_ylabel("Delhi PM2.5 (µg/m³), average day")
    ax.set_title("When the air can't rise, pollution piles up", pad=22)
    style.subtitle(ax, "Delhi winter days (Nov-Feb), split into six equal groups by mixing height.")
    style.source_note(fig)
    return fig
