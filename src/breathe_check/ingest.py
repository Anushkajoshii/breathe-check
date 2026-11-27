"""Command line for collecting data.

Examples:
    uv run python -m breathe_check.ingest stations
    uv run python -m breathe_check.ingest air --kind days --start 2018-01-01
    uv run python -m breathe_check.ingest air --kind hours --start 2025-02-01 --per-city 4
    uv run python -m breathe_check.ingest weather --start 2018-01-01
    uv run python -m breathe_check.ingest fires --start 2018-09-01
    uv run python -m breathe_check.ingest upload
"""

import argparse
from datetime import UTC, date, datetime, timedelta

import httpx
import pandas as pd

from breathe_check import settings, storage
from breathe_check.cities import CITIES, City, get_city
from breathe_check.http import RateLimiter
from breathe_check.sources import firms, openaq, weather

STATIONS_FILE = "stations.csv"


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def pick_cities(slugs: list[str] | None) -> list[City]:
    return [get_city(s) for s in slugs] if slugs else list(CITIES)


def load_stations() -> list[openaq.Station]:
    path = settings.RAW_DIR / STATIONS_FILE
    if not path.exists():
        raise SystemExit("No station list yet. Run: python -m breathe_check.ingest stations")
    frame = pd.read_csv(path).astype(object).where(lambda f: f.notna(), None)
    stations = []
    for row in frame.to_dict("records"):
        row["pm25_sensor_ids"] = tuple(int(x) for x in str(row["pm25_sensor_ids"]).split(","))
        row["location_id"] = int(row["location_id"])
        row["is_monitor"] = bool(row["is_monitor"])
        stations.append(openaq.Station(**row))
    return stations


def recent_stations(stations, city: str, per_city: int, days: int = 30) -> list:
    """Stations still reporting in the last month, closest to the city centre first."""
    c = get_city(city)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
    live = [
        s
        for s in stations
        if s.city == city and s.last_seen and pd.Timestamp(s.last_seen) >= cutoff
    ]
    live.sort(key=lambda s: openaq.distance_km(s.lat, s.lon, c.lat, c.lon))
    return live[:per_city]


def cmd_stations(args) -> None:
    limiter = RateLimiter(per_minute=33)
    with openaq.make_client(settings.need("OPENAQ_API_KEY")) as client:
        stations = openaq.find_stations(client, pick_cities(args.cities), args.radius_km, limiter)
    frame = openaq.stations_frame(stations)
    path = settings.RAW_DIR / STATIONS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    log(f"Saved {len(frame)} stations to {path}")
    print(frame.groupby("city").size().to_string())


def cmd_air(args) -> None:
    stations = load_stations()
    cities = {c.slug for c in pick_cities(args.cities)}
    if args.kind == "hours":
        chosen = [s for c in sorted(cities) for s in recent_stations(stations, c, args.per_city)]
    else:
        chosen = [s for s in stations if s.city in cities]
    source = f"air_{'daily' if args.kind == 'days' else 'hourly'}"
    done_file = settings.RAW_DIR / "_progress" / f"{source}_{args.start}_{args.end}.txt"
    done_file.parent.mkdir(parents=True, exist_ok=True)
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    limiter = RateLimiter(per_minute=33)
    log(f"Fetching {args.kind} for {len(chosen)} stations ({len(done)} already done)")
    with openaq.make_client(settings.need("OPENAQ_API_KEY")) as client:
        for i, station in enumerate(chosen, 1):
            if str(station.location_id) in done:
                continue
            sensors = None
            if args.kind == "hours":
                # Skip retired sensors so we don't ask for months they never covered
                ranges = openaq.sensor_date_ranges(client, station.location_id, limiter)
                sensors = tuple(
                    sid for sid, rng in ranges.items() if openaq.overlaps(rng, args.start, args.end)
                )
            frame = openaq.fetch_station(
                client, station, args.kind, args.start, args.end, limiter, sensor_ids=sensors
            )
            storage.save_by_year(
                frame, source, "city", "start_utc", ["location_id", "sensor_id", "start_utc"]
            )
            with done_file.open("a") as f:
                f.write(f"{station.location_id}\n")
            log(f"{i}/{len(chosen)} {station.city}: {station.name} -> {len(frame)} rows")


def cmd_weather(args) -> None:
    with httpx.Client(timeout=120) as client:
        for city in pick_cities(args.cities):
            if args.recent:
                frame = weather.fetch_recent_and_forecast(client, city)
                source = "weather_forecast"
            else:
                frame = weather.fetch_history(client, city, args.start, args.end)
                source = "weather"
            storage.save_by_year(frame, source, "city", "time_utc", ["city", "time_utc"])
            log(f"{city.slug}: {len(frame)} hours of weather")


def cmd_fires(args) -> None:
    """Fetch one year at a time and save as we go, so a long backfill can resume."""
    key = settings.need("FIRMS_MAP_KEY")
    keys = ["latitude", "longitude", "acq_date", "acq_time"]
    this_year = datetime.now(UTC).year
    with httpx.Client(timeout=120) as client:
        for year in range(args.start.year, args.end.year + 1):
            saved = settings.RAW_DIR / "fires" / "punjab_haryana" / f"{year}.parquet"
            if saved.exists() and year < this_year and not args.refresh:
                log(f"{year}: already saved, skipping")
                continue
            a = max(args.start, date(year, 1, 1))
            b = min(args.end, date(year, 12, 31))
            frame = firms.fetch_fires(client, key, a, b)
            storage.save_by_year(frame, "fires", "region", "time_utc", keys)
            log(f"{year}: {len(frame)} fire detections")


def cmd_upload(args) -> None:
    url = storage.upload_to_hub(message=args.message)
    log(f"Uploaded to {url}")


def parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    today = datetime.now(UTC).date()
    parser = argparse.ArgumentParser(prog="breathe_check.ingest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p, start_default):
        p.add_argument("--start", type=parse_date, default=start_default)
        p.add_argument("--end", type=parse_date, default=today)
        p.add_argument("--cities", nargs="*", help="city slugs, e.g. delhi indore (default: all)")

    p = sub.add_parser("stations", help="find CPCB PM2.5 stations near each city")
    p.add_argument("--cities", nargs="*")
    p.add_argument("--radius-km", type=int, default=25)
    p.set_defaults(func=cmd_stations)

    p = sub.add_parser("air", help="PM2.5 readings from OpenAQ")
    add_common(p, today - timedelta(days=7))
    p.add_argument("--kind", choices=["days", "hours"], default="days")
    p.add_argument("--per-city", type=int, default=4, help="stations per city (hours only)")
    p.set_defaults(func=cmd_air)

    p = sub.add_parser("weather", help="hourly weather from Open-Meteo")
    add_common(p, today - timedelta(days=30))
    p.add_argument("--recent", action="store_true", help="last 7 days + next 2 days")
    p.set_defaults(func=cmd_weather)

    p = sub.add_parser("fires", help="crop fires from NASA FIRMS")
    add_common(p, today - timedelta(days=7))
    p.add_argument("--refresh", action="store_true", help="re-fetch years already saved")
    p.set_defaults(func=cmd_fires)

    p = sub.add_parser("upload", help="copy data/raw to the Hugging Face dataset")
    p.add_argument("--message", default="Update data")
    p.set_defaults(func=cmd_upload)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
