"""Crop-fire detections from NASA FIRMS (VIIRS satellite, free key).

Every October-November, farmers in Punjab and Haryana burn rice stubble. Smoke
can drift to Delhi when the wind blows from the north-west. We count fires in a
box around the two states, and later pair the counts with wind direction.

FIRMS has two versions of the same data:
- SP (standard): checked and final, available up to about 2-3 months ago.
- NRT (near real-time): within hours, for recent days.
"""

import io
import time
from datetime import date, timedelta

import httpx
import pandas as pd

from breathe_check.http import get_with_retry

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
MAX_DAYS_PER_CALL = 5  # the API refuses more than 5 days per call

# FIRMS allows 5000 "transactions" per 10 minutes; each call costs several.
LIMIT_MESSAGE = "exceeding allowed transaction limit"

# west, south, east, north: Punjab and Haryana
REGIONS = {"punjab_haryana": (73.8, 27.6, 77.6, 32.6)}


def get_csv(client: httpx.Client, url: str, sleep=time.sleep, max_waits: int = 15) -> str:
    """GET a FIRMS CSV. If we hit the 10-minute limit, wait a minute and try again."""
    for _ in range(max_waits + 1):
        response = client.get(url)
        if LIMIT_MESSAGE in response.text[:200].lower():
            sleep(60)
            continue
        response.raise_for_status()
        return response.text
    raise RuntimeError("FIRMS transaction limit did not reset in time")


def parse_csv(text: str) -> pd.DataFrame:
    text = text.strip()
    if not text or not text.startswith("latitude"):
        # FIRMS returns a plain message (not CSV) when something is wrong
        if text and "invalid" in text.lower():
            raise ValueError(f"FIRMS error: {text[:200]}")
        return pd.DataFrame()
    frame = pd.read_csv(io.StringIO(text))
    # Final data says "2", near-real-time says "2.0NRT"; keep it as text
    frame["version"] = frame["version"].astype(str)
    frame["confidence"] = frame["confidence"].astype(str)
    hhmm = frame["acq_time"].astype(int).astype(str).str.zfill(4)
    frame["time_utc"] = pd.to_datetime(
        frame["acq_date"] + " " + hhmm.str[:2] + ":" + hhmm.str[2:], utc=True
    )
    return frame


def last_days(client: httpx.Client, key: str) -> dict[str, date]:
    """The last day each FIRMS data source covers, e.g. {"VIIRS_SNPP_SP": 2026-08-31}."""
    response = get_with_retry(client, f"{BASE_URL}/data_availability/csv/{key}/all")
    frame = pd.read_csv(io.StringIO(response.text))
    return {row.data_id: date.fromisoformat(str(row.max_date)) for row in frame.itertuples()}


def pick_source(chunk_end: date, last: dict[str, date]) -> str:
    """Which satellite feed to use for a chunk of days.

    Suomi NPP is the long, consistent record (final data, then near-real-time).
    Its near-real-time feed stopped on 2 November 2026, so for later days we use
    NOAA-20, which carries the same VIIRS instrument.
    """
    if chunk_end <= last.get("VIIRS_SNPP_SP", date.min):
        return "VIIRS_SNPP_SP"
    if chunk_end <= last.get("VIIRS_SNPP_NRT", date.min):
        return "VIIRS_SNPP_NRT"
    return "VIIRS_NOAA20_NRT"


def date_chunks(start: date, end: date, size: int = MAX_DAYS_PER_CALL):
    day = start
    while day <= end:
        last = min(end, day + timedelta(days=size - 1))
        yield day, (last - day).days + 1
        day = last + timedelta(days=1)


def fetch_fires(
    client: httpx.Client,
    key: str,
    start: date,
    end: date,
    region: str = "punjab_haryana",
    sleep=time.sleep,
) -> pd.DataFrame:
    """All fire detections in a region between two dates (inclusive)."""
    west, south, east, north = REGIONS[region]
    area = f"{west},{south},{east},{north}"
    last = last_days(client, key)
    parts = []
    for first_day, days in date_chunks(start, end):
        source = pick_source(first_day + timedelta(days=days - 1), last)
        url = f"{BASE_URL}/area/csv/{key}/{source}/{area}/{days}/{first_day.isoformat()}"
        frame = parse_csv(get_csv(client, url, sleep=sleep))
        if not frame.empty:
            frame["source"] = source
            parts.append(frame)
    if not parts:
        return pd.DataFrame()
    fires = pd.concat(parts, ignore_index=True)
    fires.insert(0, "region", region)
    keys = ["latitude", "longitude", "acq_date", "acq_time"]
    return fires.drop_duplicates(keys).reset_index(drop=True)
