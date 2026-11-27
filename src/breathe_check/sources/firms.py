"""Crop-fire detections from NASA FIRMS (VIIRS satellite, free key).

Every October-November, farmers in Punjab and Haryana burn rice stubble. Smoke
can drift to Delhi when the wind blows from the north-west. We count fires in a
box around the two states, and later pair the counts with wind direction.

FIRMS has two versions of the same data:
- SP (standard): checked and final, available up to about 2-3 months ago.
- NRT (near real-time): within hours, for recent days.
"""

import io
from datetime import date, timedelta

import httpx
import pandas as pd

from breathe_check.http import get_with_retry

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
MAX_DAYS_PER_CALL = 5  # the API refuses more than 5 days per call

# west, south, east, north: Punjab and Haryana
REGIONS = {"punjab_haryana": (73.8, 27.6, 77.6, 32.6)}


def parse_csv(text: str) -> pd.DataFrame:
    text = text.strip()
    if not text or not text.startswith("latitude"):
        # FIRMS returns a plain message (not CSV) when something is wrong
        if text and "invalid" in text.lower():
            raise ValueError(f"FIRMS error: {text[:200]}")
        return pd.DataFrame()
    frame = pd.read_csv(io.StringIO(text))
    hhmm = frame["acq_time"].astype(int).astype(str).str.zfill(4)
    frame["time_utc"] = pd.to_datetime(
        frame["acq_date"] + " " + hhmm.str[:2] + ":" + hhmm.str[2:], utc=True
    )
    return frame


def sp_last_day(client: httpx.Client, key: str, source: str = "VIIRS_SNPP_SP") -> date:
    """The last day the standard (final) data covers."""
    response = get_with_retry(client, f"{BASE_URL}/data_availability/csv/{key}/{source}")
    frame = pd.read_csv(io.StringIO(response.text))
    return date.fromisoformat(str(frame["max_date"].iloc[0]))


def date_chunks(start: date, end: date, size: int = MAX_DAYS_PER_CALL):
    day = start
    while day <= end:
        last = min(end, day + timedelta(days=size - 1))
        yield day, (last - day).days + 1
        day = last + timedelta(days=1)


def fetch_fires(
    client: httpx.Client, key: str, start: date, end: date, region: str = "punjab_haryana"
) -> pd.DataFrame:
    """All fire detections in a region between two dates (inclusive)."""
    west, south, east, north = REGIONS[region]
    area = f"{west},{south},{east},{north}"
    cutoff = sp_last_day(client, key)
    parts = []
    for first_day, days in date_chunks(start, end):
        source = (
            "VIIRS_SNPP_SP" if first_day + timedelta(days=days - 1) <= cutoff else "VIIRS_SNPP_NRT"
        )
        url = f"{BASE_URL}/area/csv/{key}/{source}/{area}/{days}/{first_day.isoformat()}"
        frame = parse_csv(get_with_retry(client, url).text)
        if not frame.empty:
            frame["source"] = source
            parts.append(frame)
    if not parts:
        return pd.DataFrame()
    fires = pd.concat(parts, ignore_index=True)
    fires.insert(0, "region", region)
    keys = ["latitude", "longitude", "acq_date", "acq_time"]
    return fires.drop_duplicates(keys).reset_index(drop=True)
