"""Part 8: Indore is India's cleanest city by its waste ranking. Is its air clean?

Three questions:
1. How does Indore's PM2.5 compare with India's limits and the WHO guideline?
2. How does it compare with similar cities nearby (Bhopal, Jaipur, Nagpur, Ahmedabad)?
3. Is Indore cleaner only because of its weather? We answer this with one shared
   weather model for all 20 cities: it predicts PM2.5 from weather alone, the
   same way for everyone. A city's actual / predicted ratio then says how dirty
   it is *for its weather*. Below 1 = cleaner than its weather would suggest.
"""

import numpy as np
import pandas as pd

from breathe_check.analysis import deweather as dw
from breathe_check.standards import (
    AQI_BANDS,
    INDIA_ANNUAL_PM25,
    INDIA_DAILY_PM25,
    PM25_PER_CIGARETTE,
    WHO_ANNUAL_PM25,
    WHO_DAILY_PM25,
    aqi_band,
)

PEERS = ["indore", "bhopal", "jaipur", "nagpur", "ahmedabad"]
CONTEXT = ["delhi", "bengaluru"]
FULL_SEASON_DAYS = 300  # a season (July-June) needs this many days with data to count


def with_season(city_day: pd.DataFrame) -> pd.DataFrame:
    df = city_day.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["season"] = dw.season_of(df["date"])
    return df[df["pm25"].notna()]


def season_summary(city_day: pd.DataFrame, cities: list[str]) -> pd.DataFrame:
    """Yearly picture for each city and each nearly-complete season (July-June)."""
    df = with_season(city_day)
    df = df[df["city"].isin(cities)]
    g = df.groupby(["city", "season"])
    out = g.agg(
        days=("pm25", "size"),
        pm25=("pm25", "mean"),
        stations=("n_stations", "mean"),
        days_over_india=("pm25", lambda s: int((s > INDIA_DAILY_PM25).sum())),
        days_over_who=("pm25", lambda s: int((s > WHO_DAILY_PM25).sum())),
    ).reset_index()
    out = out[out["days"] >= FULL_SEASON_DAYS].copy()
    out["times_india_limit"] = out["pm25"] / INDIA_ANNUAL_PM25
    out["times_who_guideline"] = out["pm25"] / WHO_ANNUAL_PM25
    out["cigarettes_a_day"] = out["pm25"] / PM25_PER_CIGARETTE
    out["share_days_over_india"] = out["days_over_india"] / out["days"]
    out["share_days_over_who"] = out["days_over_who"] / out["days"]
    return out.sort_values(["season", "pm25"]).reset_index(drop=True)


def band_days(city_day: pd.DataFrame, cities: list[str], season: str) -> pd.DataFrame:
    """Share of days in each India AQI category (Good, Satisfactory, ...)."""
    df = with_season(city_day)
    df = df[df["city"].isin(cities) & (df["season"] == season)].copy()
    df["band"] = df["pm25"].map(lambda v: aqi_band(max(v, 0)).name)
    order = [b.name for b in AQI_BANDS]
    counts = (
        df.groupby(["city", "band"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=order, fill_value=0)
    )
    return counts.div(counts.sum(axis=1), axis=0).reset_index()


def weather_fair(city_day: pd.DataFrame, season: str) -> pd.DataFrame:
    """One shared weather-only model for all cities; each city's median ratio of
    actual to what that model predicts, for one season.

    The shared model never sees which city it is predicting, so cities are judged
    against the same weather-to-PM2.5 relationship. Every prediction comes from a
    model trained without that season."""
    features = dw.add_features(city_day)
    pooled = dw.deweather_city(features).predictions
    p = pooled[pooled["season"] == season].copy()
    p["ratio"] = p["pm25"] / p["expected"]
    out = (
        p.groupby("city")
        .agg(
            ratio=("ratio", "median"),
            actual=("pm25", "mean"),
            expected=("expected", "mean"),
            days=("pm25", "size"),
        )
        .reset_index()
    )
    out["vs_weather_pct"] = (out["ratio"] - 1) * 100
    return out.sort_values("ratio").reset_index(drop=True)


def same_station(flagged: pd.DataFrame, location_id: int, seasons: list[str]) -> pd.DataFrame:
    """One station's clean daily average in each season, for a like-for-like trend."""
    df = flagged[flagged["location_id"] == location_id].copy()
    flags = [
        "flag_impossible",
        "flag_incomplete",
        "flag_flat",
        "flag_repeated",
        "flag_city_outlier",
    ]
    df = df[~df[flags].any(axis=1)]
    df["date"] = pd.to_datetime(df["date"])
    df["season"] = dw.season_of(df["date"])
    df = df[df["season"].isin(seasons)]
    out = df.groupby("season").agg(pm25=("pm25", "mean"), days=("pm25", "size")).reset_index()
    out["change_pct"] = (out["pm25"] / out["pm25"].iloc[0] - 1) * 100
    return out


def winter_vs_rest(city_day: pd.DataFrame, cities: list[str], season: str) -> pd.DataFrame:
    df = with_season(city_day)
    df = df[df["city"].isin(cities) & (df["season"] == season)].copy()
    df["part"] = np.where(df["date"].dt.month.isin([11, 12, 1, 2]), "winter", "rest")
    return df.pivot_table(index="city", columns="part", values="pm25", aggfunc="mean").reset_index()
