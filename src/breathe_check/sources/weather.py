"""Hourly weather from Open-Meteo (free, no key).

Weather explains most day-to-day swings in PM2.5: calm wind, low "mixing height"
(boundary layer) and no rain trap pollution near the ground. We need it to
separate the effect of weather from the effect of rules like GRAP.

- Archive API (ERA5 reanalysis): the past, up to about 5 days ago.
- Forecast API: the last few days and the next two days.
"""

from datetime import date

import httpx
import pandas as pd

from breathe_check.cities import City
from breathe_check.http import get_with_retry

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARS = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "boundary_layer_height",
    "shortwave_radiation",
)


def parse_hourly(payload: dict, city: City) -> pd.DataFrame:
    hourly = payload.get("hourly") or {}
    if not hourly.get("time"):
        return pd.DataFrame()
    frame = pd.DataFrame(hourly)
    frame["time_utc"] = pd.to_datetime(frame.pop("time"), utc=True)
    frame.insert(0, "city", city.slug)
    return frame


def fetch_history(client: httpx.Client, city: City, start: date, end: date) -> pd.DataFrame:
    """Past hourly weather for one city, asked for one year at a time."""
    parts = []
    for year in range(start.year, end.year + 1):
        a = max(start, date(year, 1, 1))
        b = min(end, date(year, 12, 31))
        response = get_with_retry(
            client,
            ARCHIVE_URL,
            params={
                "latitude": city.lat,
                "longitude": city.lon,
                "start_date": a.isoformat(),
                "end_date": b.isoformat(),
                "hourly": ",".join(HOURLY_VARS),
                "timezone": "GMT",
            },
        )
        parts.append(parse_hourly(response.json(), city))
    parts = [p for p in parts if not p.empty]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def fetch_recent_and_forecast(
    client: httpx.Client, city: City, past_days: int = 7, forecast_days: int = 3
) -> pd.DataFrame:
    """The last few days (to fill the archive's delay) plus today and the next two days."""
    response = get_with_retry(
        client,
        FORECAST_URL,
        params={
            "latitude": city.lat,
            "longitude": city.lon,
            "hourly": ",".join(HOURLY_VARS),
            "past_days": past_days,
            "forecast_days": forecast_days,
            "timezone": "GMT",
        },
    )
    return parse_hourly(response.json(), city)
