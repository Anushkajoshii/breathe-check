"""Make tomorrow's run-window forecast for every city, as small JSON files.

    uv run python -m breathe_check.forecast

Reads the clean tables (city_hour for today's air, weather_hour for tomorrow's
weather, city_day for fires), trains the forecast models, and writes:

    data/public/forecast/<city>.json   one file per city
    data/public/forecast/index.json    list of cities and when this was made

The web app and the calendar feed read these files.
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd

from breathe_check import settings
from breathe_check.analysis import run_window as rw
from breathe_check.analysis.load import load
from breathe_check.cities import CITIES, DEFAULT_CITY
from breathe_check.standards import aqi_band

OUT = settings.DATA_DIR / "public" / "forecast"
NCR_ROLE = "grap"


def now_ist() -> pd.Timestamp:
    return pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)


def tomorrow_rows(weather_hour: pd.DataFrame, today_level: pd.DataFrame, day: pd.Timestamp):
    """Rows for every city and hour of `day`, ready for the models."""
    w = weather_hour[pd.to_datetime(weather_hour["date"]) == day].copy()
    w["time_ist"] = pd.to_datetime(w["date"]) + pd.to_timedelta(w["hour"], unit="h")
    w = rw.add_wind_parts(w)
    doy = w["time_ist"].dt.day_of_year
    w["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    w["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    w["weekday"] = w["time_ist"].dt.day_of_week
    w = w.merge(today_level, on="city", how="left")
    return w


def latest_level(city_hour: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Today's midnight-to-6pm average and 5 pm reading per city. If today has no
    data yet for a city, fall back to its most recent day, and say which day."""
    levels = rw.today_to_6pm(city_hour)
    levels = levels[levels["date"] <= today].sort_values("date").groupby("city").tail(1)
    return levels.rename(columns={"date": "level_from"})


def nw_share(weather_hour: pd.DataFrame, city: str, day: pd.Timestamp) -> float:
    w = weather_hour[(weather_hour["city"] == city) & (pd.to_datetime(weather_hour["date"]) == day)]
    if w.empty:
        return 0.0
    return float(w["wind_dir_deg"].between(270, 360).mean())


def city_payload(city, hours: pd.DataFrame, level: pd.Series, today_mean, smoke, scores) -> dict:
    hours = hours.sort_values("hour")
    best = rw.best_window(hours, "mid")
    worst_start = int(hours.loc[hours["mid"].idxmax(), "hour"])
    best_band = aqi_band(best["pm25"]) if best else None
    return {
        "city": city.slug,
        "name": city.name,
        "state": city.state,
        "for_date": str(hours["time_ist"].iloc[0].date()),
        "hours": [
            {
                "hour": int(r.hour),
                "low": round(float(r.low), 1),
                "mid": round(float(r.mid), 1),
                "high": round(float(r.high), 1),
                "category": aqi_band(float(r.mid)).name,
            }
            for r in hours.itertuples()
        ],
        "best_window": None
        if best is None
        else {
            "start": best["start"],
            "end": best["end"],
            "pm25": round(best["pm25"], 1),
            "category": best_band.name,
            "advice": best_band.advice,
        },
        "worst_hour": worst_start,
        "today": None if today_mean is None else rw.cigarette_card(today_mean),
        "based_on_air_up_to": str(pd.Timestamp(level["level_from"]).date())
        if level is not None
        else None,
        "smoke": smoke,
        "how_good": scores,
    }


def main() -> None:
    made_at = now_ist()
    today = made_at.normalize()
    tomorrow = today + pd.Timedelta(days=1)

    city_hour = load("city_hour")
    weather_hour = load("weather_hour")
    fires_day = load("fires_day")

    rows = rw.build_rows(city_hour)
    models, widen = rw.fit_with_calibration(rows)

    level = latest_level(city_hour, today)
    future = tomorrow_rows(weather_hour, level, tomorrow)
    future["city"] = pd.Categorical(future["city"], categories=rows["city"].cat.categories)
    pred = rw.predict(models, future.dropna(subset=["pm_today_to_6pm"]), widen)

    # "Today" card: the last 24 hours each city has data for
    ch = city_hour.copy()
    ch["time_ist"] = pd.to_datetime(ch["time_ist"])
    latest = ch.groupby("city")["time_ist"].transform("max")
    last_day = ch[ch["time_ist"] > latest - pd.Timedelta(hours=24)]
    today_means = last_day.groupby("city")["pm25"].mean()
    today_until = ch.groupby("city")["time_ist"].max()

    # Fires: the most recent day the satellite data covers
    fires_day["date"] = pd.to_datetime(fires_day["date"])
    recent_fires = fires_day[fires_day["date"] <= today].sort_values("date").tail(1)
    if len(recent_fires):
        fires_count = int(recent_fires["fires_confident"].iloc[0])
        fires_date = f"on {recent_fires['date'].iloc[0]:%d %b}"
    else:
        fires_count, fires_date = 0, "recently"

    scores = {"range_holds_real_value": "about 80% of hours", "range_widening": round(widen, 2)}

    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for city in CITIES:
        hours = pred[pred["city"] == city.slug]
        if len(hours) < 18:
            continue
        lvl = level[level["city"] == city.slug]
        lvl = lvl.iloc[0] if len(lvl) else None
        smoke = None
        if city.role == NCR_ROLE:
            share = nw_share(weather_hour, city.slug, tomorrow)
            smoke = rw.smoke_check(fires_count, share, tomorrow.month, fires_date)
        payload = city_payload(city, hours, lvl, today_means.get(city.slug), smoke, scores)
        if payload["today"] is not None:
            payload["today"]["label"] = "Last 24 hours"
            payload["today"]["until"] = today_until[city.slug].isoformat(timespec="minutes")
        payload["made_at"] = made_at.isoformat(timespec="minutes")
        (OUT / f"{city.slug}.json").write_text(json.dumps(payload, indent=1))
        index.append(
            {
                "city": city.slug,
                "name": city.name,
                "state": city.state,
                "best_window": payload["best_window"],
            }
        )
    (OUT / "index.json").write_text(
        json.dumps(
            {
                "made_at": made_at.isoformat(timespec="minutes"),
                "for_date": str(tomorrow.date()),
                "default_city": DEFAULT_CITY,
                "cities": index,
            },
            indent=1,
        )
    )
    print(
        f"[{datetime.now():%H:%M:%S}] wrote {len(index)} forecasts for {tomorrow.date()} to {OUT}"
    )


if __name__ == "__main__":
    main()
