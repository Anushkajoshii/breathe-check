"""The daily update: what the GitHub Actions job runs every evening.

    uv run python -m breathe_check.daily            # everything
    uv run python -m breathe_check.daily --no-pull  # use the data already on disk
    uv run python -m breathe_check.daily --no-upload

Steps:
 1. pull      download the raw data so far from Hugging Face
 2. fetch     the last 7 days of PM2.5 (daily and hourly), weather, the weather
              forecast, and crop fires
 3. clean     run the dbt cleaning rules and rebuild the clean tables
 4. forecast  make tomorrow's run-window forecast for every city
    calendar  add tomorrow's best window to each city's calendar feed (.ics)
 5. status    write data/public/status.json: when this ran, how fresh each source is
 6. upload    push raw, clean and public files back to Hugging Face

If one data source fails (an API is down), the others still run, the forecast is
still made from whatever is newest, and status.json says what failed. The job
only fails outright if cleaning or the forecast fails.
"""

import argparse
import json
import os
import subprocess
import sys
import traceback
from datetime import UTC, datetime, timedelta

import pandas as pd

from breathe_check import calendar_feed, forecast, ingest, settings, storage

FETCH_STEPS = [
    ("air_daily", ["air", "--kind", "days"]),
    ("air_hourly", ["air", "--kind", "hours"]),
    ("weather", ["weather"]),
    ("weather_forecast", ["weather", "--recent"]),
    ("fires", ["fires", "--refresh"]),
]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def run_step(name: str, fn, status: dict) -> bool:
    log(f"--- {name}")
    try:
        fn()
        status["steps"][name] = "ok"
        return True
    except Exception as exc:  # keep going; record what broke
        status["steps"][name] = f"failed: {type(exc).__name__}: {exc}"[:300]
        traceback.print_exc()
        return False


def fetch(args_list: list[str]) -> None:
    today = datetime.now(UTC).date()
    start = (today - timedelta(days=7)).isoformat()
    extra = [] if args_list[0] == "weather" and "--recent" in args_list else ["--start", start]
    if args_list[0] == "fires":
        extra = ["--start", (today - timedelta(days=4)).isoformat()]
    ingest.main([*args_list, *extra])


def clean() -> None:
    (settings.DATA_DIR / "clean").mkdir(parents=True, exist_ok=True)
    cmd = ["dbt", "build", "--project-dir", "transform", "--profiles-dir", "transform"]
    result = subprocess.run(cmd, cwd=settings.ROOT, capture_output=True, text=True)
    print(result.stdout[-4000:])
    if result.returncode != 0:
        raise RuntimeError("dbt build failed")


def freshness() -> dict:
    """Latest timestamp in each clean table, so anyone can see how fresh the data is."""
    out = {}
    clean = settings.DATA_DIR / "clean"
    checks = {
        "air_hourly_latest": ("city_hour.parquet", "time_ist"),
        "air_daily_latest": ("city_day.parquet", "date"),
        "weather_latest": ("weather_hour.parquet", "time_ist"),
        "fires_latest": ("fires_day.parquet", "date"),
    }
    for key, (file, col) in checks.items():
        path = clean / file
        if path.exists():
            frame = pd.read_parquet(
                path, columns=[col, *(["pm25"] if file == "city_day.parquet" else [])]
            )
            if file == "city_day.parquet":
                frame = frame[frame["pm25"].notna()]
            out[key] = str(pd.to_datetime(frame[col]).max())
    return out


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # keep the logs readable
    parser = argparse.ArgumentParser(prog="breathe_check.daily")
    parser.add_argument("--no-pull", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args(argv)

    status = {"started_at": datetime.now(UTC).isoformat(timespec="seconds"), "steps": {}}
    if not args.no_pull:
        # raw data, plus the calendar history so each feed keeps its last 14 days
        patterns = ("raw/*", "raw/**", "public/calendar/*.json")
        run_step("pull", lambda: storage.pull_from_hub(patterns), status)
    for name, step in FETCH_STEPS:
        run_step(f"fetch_{name}", lambda step=step: fetch(step), status)
    ok = run_step("clean", clean, status) and run_step("forecast", forecast.main, status)
    if ok:
        # a calendar problem is recorded but doesn't block the forecast
        run_step("calendar", calendar_feed.main, status)

    status["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    status["data_up_to"] = freshness()
    status["ok"] = ok and all(v == "ok" for v in status["steps"].values())
    public = settings.DATA_DIR / "public"
    public.mkdir(parents=True, exist_ok=True)
    (public / "status.json").write_text(json.dumps(status, indent=1))
    log(json.dumps(status, indent=1))

    if not args.no_upload and ok:
        run_step(
            "upload",
            lambda: storage.upload_to_hub(message=f"Daily update {status['started_at'][:10]}"),
            status,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
