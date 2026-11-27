"""PM2.5 from India's government (CPCB) monitoring stations, via the OpenAQ API.

OpenAQ copies CPCB readings and serves them through one tidy API. We use:
- /v3/locations   to find stations near each city
- /v3/sensors/{id}/days   for daily averages (the long history we analyse)
- /v3/sensors/{id}/hours  for hourly values (the run-window forecast)

Known gap: OpenAQ has almost no CPCB data from November 2022 to February 2025.
See docs/data-card.md.
"""

import math
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime

import httpx
import pandas as pd

from breathe_check.cities import CITIES, City
from breathe_check.http import RateLimiter, get_with_retry

BASE_URL = "https://api.openaq.org/v3"
PM25_PARAMETER_ID = 2
PAGE_SIZE = 1000


@dataclass(frozen=True)
class Station:
    location_id: int
    name: str
    city: str
    provider: str
    owner: str
    lat: float
    lon: float
    is_monitor: bool
    pm25_sensor_ids: tuple[int, ...]
    first_seen: str | None
    last_seen: str | None


def make_client(api_key: str) -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, headers={"X-API-Key": api_key}, timeout=60)


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance on the Earth's surface (haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_city(lat: float, lon: float, cities=CITIES) -> City:
    return min(cities, key=lambda c: distance_km(lat, lon, c.lat, c.lon))


def parse_locations(payload: dict, city: City) -> list[Station]:
    """Keep only fixed government (CPCB) stations that measure PM2.5."""
    stations = []
    for loc in payload.get("results", []):
        provider = (loc.get("provider") or {}).get("name", "")
        if provider != "CPCB" or loc.get("isMobile"):
            continue
        sensor_ids = tuple(
            s["id"] for s in loc.get("sensors", []) if s["parameter"]["id"] == PM25_PARAMETER_ID
        )
        if not sensor_ids:
            continue
        coords = loc.get("coordinates") or {}
        stations.append(
            Station(
                location_id=loc["id"],
                name=loc["name"],
                city=city.slug,
                provider=provider,
                owner=(loc.get("owner") or {}).get("name", ""),
                lat=coords.get("latitude"),
                lon=coords.get("longitude"),
                is_monitor=bool(loc.get("isMonitor")),
                pm25_sensor_ids=sensor_ids,
                first_seen=(loc.get("datetimeFirst") or {}).get("utc"),
                last_seen=(loc.get("datetimeLast") or {}).get("utc"),
            )
        )
    return stations


def find_stations(
    client: httpx.Client, cities=CITIES, radius_km: int = 25, limiter: RateLimiter | None = None
) -> list[Station]:
    """Find CPCB PM2.5 stations near each city.

    Delhi-NCR cities are close together, so one station can be near several of
    them. Each station is given to the single city it is closest to.
    """
    found: dict[int, Station] = {}
    for city in cities:
        if limiter:
            limiter.wait()
        response = get_with_retry(
            client,
            "/locations",
            params={
                "coordinates": f"{city.lat},{city.lon}",
                "radius": radius_km * 1000,
                "parameters_id": PM25_PARAMETER_ID,
                "limit": 1000,
            },
        )
        for station in parse_locations(response.json(), city):
            owner = nearest_city(station.lat, station.lon, cities)
            if owner.slug == city.slug:
                found[station.location_id] = station
    return sorted(found.values(), key=lambda s: (s.city, s.location_id))


def stations_frame(stations: list[Station]) -> pd.DataFrame:
    rows = [
        {**s.__dict__, "pm25_sensor_ids": ",".join(map(str, s.pm25_sensor_ids))} for s in stations
    ]
    return pd.DataFrame(rows)


def parse_measurements(payload: dict) -> list[dict]:
    """Turn one page of /hours or /days results into flat rows."""
    rows = []
    for item in payload.get("results", []):
        period = item["period"]
        summary = item.get("summary") or {}
        coverage = item.get("coverage") or {}
        rows.append(
            {
                "period": period["label"],
                "start_utc": period["datetimeFrom"]["utc"],
                "start_local": period["datetimeFrom"]["local"],
                "value": item["value"],
                "min": summary.get("min"),
                "max": summary.get("max"),
                "sd": summary.get("sd"),
                "observed_count": coverage.get("observedCount"),
                "percent_complete": coverage.get("percentComplete"),
                "has_flags": bool((item.get("flagInfo") or {}).get("hasFlags")),
            }
        )
    return rows


def iter_sensor_pages(
    client: httpx.Client,
    sensor_id: int,
    kind: str,
    start: date | datetime,
    end: date | datetime,
    limiter: RateLimiter | None = None,
) -> Iterator[list[dict]]:
    """Yield pages of readings for one sensor. kind is "days" or "hours"."""
    if kind == "days":
        params = {"date_from": str(start)[:10], "date_to": str(end)[:10]}
    elif kind == "hours":
        params = {
            "datetime_from": pd.Timestamp(start).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "datetime_to": pd.Timestamp(end).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    else:
        raise ValueError("kind must be 'days' or 'hours'")
    page = 1
    while True:
        if limiter:
            limiter.wait()
        response = get_with_retry(
            client,
            f"/sensors/{sensor_id}/{kind}",
            params={**params, "limit": PAGE_SIZE, "page": page},
        )
        rows = parse_measurements(response.json())
        if rows:
            yield rows
        if len(rows) < PAGE_SIZE:
            return
        page += 1


def sensor_date_ranges(
    client: httpx.Client, location_id: int, limiter: RateLimiter | None = None
) -> dict[int, tuple[pd.Timestamp | None, pd.Timestamp | None]]:
    """First and last reading time of each PM2.5 sensor at a station."""
    if limiter:
        limiter.wait()
    payload = get_with_retry(client, f"/locations/{location_id}/sensors").json()
    ranges = {}
    for s in payload.get("results", []):
        if s["parameter"]["id"] != PM25_PARAMETER_ID:
            continue
        first = (s.get("datetimeFirst") or {}).get("utc")
        last = (s.get("datetimeLast") or {}).get("utc")
        ranges[s["id"]] = (
            pd.Timestamp(first) if first else None,
            pd.Timestamp(last) if last else None,
        )
    return ranges


def overlaps(rng, start, end) -> bool:
    """Does a sensor's (first, last) range overlap [start, end]? Unknown means yes."""
    first, last = rng
    start, end = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    return (first is None or first <= end) and (last is None or last >= start)


def month_windows(start, end) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Split a time range into calendar months. Deep pages time out on OpenAQ,
    so we ask for one month of hourly data at a time (one or two pages each)."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    edges = [
        start,
        *pd.date_range(start.normalize() + pd.offsets.MonthBegin(1), end, freq="MS"),
        end,
    ]
    return [(a, b) for a, b in zip(edges, edges[1:], strict=False) if a < b]


def fetch_station(
    client: httpx.Client,
    station: Station,
    kind: str,
    start: date | datetime,
    end: date | datetime,
    limiter: RateLimiter | None = None,
    sensor_ids: tuple[int, ...] | None = None,
) -> pd.DataFrame:
    """All PM2.5 readings for one station, from all (or the given) sensors, as a table."""
    windows = month_windows(start, end) if kind == "hours" else [(start, end)]
    rows = []
    for sensor_id in sensor_ids if sensor_ids is not None else station.pm25_sensor_ids:
        for a, b in windows:
            for page in iter_sensor_pages(client, sensor_id, kind, a, b, limiter):
                for row in page:
                    rows.append({"sensor_id": sensor_id, **row})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame.insert(0, "location_id", station.location_id)
    frame.insert(0, "city", station.city)
    frame["start_utc"] = pd.to_datetime(frame["start_utc"], utc=True)
    # The API sometimes returns the same period twice; keep one.
    frame = frame.drop_duplicates(["sensor_id", "start_utc"]).sort_values("start_utc")
    return frame.reset_index(drop=True)
