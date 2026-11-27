"""A tiny fake raw dataset with known problems planted in it.

The dbt tests run the real cleaning rules on this and check that each rule
catches exactly the readings we broke on purpose, and nothing else.
"""

from pathlib import Path

import numpy as np
import pandas as pd

DAYS = pd.date_range("2025-11-06", "2025-11-15", freq="D")


def daily_rows(location_id, values, sd=10.0, pct=100.0, city="delhi"):
    rows = []
    for day, value in zip(DAYS, values, strict=True):
        rows.append(
            {
                "city": city,
                "location_id": location_id,
                "sensor_id": location_id * 10,
                "period": "1day",
                "start_utc": (day - pd.Timedelta(minutes=330)).tz_localize("UTC"),
                "start_local": day.strftime("%Y-%m-%dT00:00:00+05:30"),
                "value": value,
                "min": value - 5,
                "max": value + 5,
                "sd": sd,
                "observed_count": 24,
                "percent_complete": pct,
                "has_flags": False,
            }
        )
    return rows


def make_raw(root: Path) -> None:
    root = Path(root)

    # --- daily PM2.5: Delhi has 4 stations; station 4 is the broken one ---
    rows = []
    rows += daily_rows(1, [100 + i for i in range(10)])
    rows += daily_rows(2, [110 + i for i in range(10)])
    rows += daily_rows(3, [105.0] * 2 + [106 + i for i in range(8)])
    bad = daily_rows(4, [120 + i for i in range(10)])
    bad[2]["value"] = -5  # 2025-11-08 impossible
    bad[3]["percent_complete"] = 40  # 2025-11-09 incomplete
    bad[4]["sd"] = 0  # 2025-11-10 flat (stuck all day)
    for i in (5, 6, 7):  # 2025-11-11 to 13 repeated
        bad[i]["value"] = 77.7
    bad[9]["value"] = 900  # 2025-11-15 far above the other stations
    rows += bad
    rows += daily_rows(9, [40 + i for i in range(10)], city="indore")
    daily = pd.DataFrame(rows)
    for city, part in daily.groupby("city"):
        path = root / "air_daily" / city / "2025.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        part.to_parquet(path, index=False)

    # --- hourly PM2.5 for one Delhi station, 48 hours ---
    hours = pd.date_range("2025-11-06 00:00", periods=48, freq="h")  # India time
    values = 50 + 5 * np.sin(np.arange(48) / 3)
    values[10:16] = 42.0  # stuck for 6 hours
    values[30] = 400.0  # spike
    values[44] = 1200.0  # impossible
    pct = np.full(48, 100.0)
    pct[40] = 25.0  # incomplete
    hourly = pd.DataFrame(
        {
            "city": "delhi",
            "location_id": 1,
            "sensor_id": 10,
            "period": "1hour",
            "start_utc": (hours - pd.Timedelta(minutes=330)).tz_localize("UTC"),
            "start_local": hours.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "value": values,
            "min": values,
            "max": values,
            "sd": 1.0,
            "observed_count": 4,
            "percent_complete": pct,
            "has_flags": False,
        }
    )
    path = root / "air_hourly" / "delhi" / "2025.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_parquet(path, index=False)

    # --- weather: every UTC hour across the window, for Delhi and Indore ---
    times = pd.date_range("2025-11-05 00:00", "2025-11-16 23:00", freq="h", tz="UTC")
    for city in ("delhi", "indore"):
        weather = pd.DataFrame(
            {
                "temperature_2m": 20.0,
                "relative_humidity_2m": 60.0,
                "dew_point_2m": 12.0,
                "precipitation": 0.0,
                "surface_pressure": 990.0,
                "cloud_cover": 10.0,
                "wind_speed_10m": 8.0,
                "wind_direction_10m": 315.0,  # from the north-west
                "wind_gusts_10m": 15.0,
                "boundary_layer_height": 400.0,
                "shortwave_radiation": 100.0,
            },
            index=range(len(times)),
        )
        weather["time_utc"] = times
        weather.insert(0, "city", city)
        for folder in ("weather", "weather_forecast"):
            path = root / folder / city / "2025.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            (weather if folder == "weather" else weather.tail(1)).to_parquet(path, index=False)

    # --- fires: 3 on 2025-11-10 (one low confidence), 1 on 2025-11-11 ---
    fires = pd.DataFrame(
        {
            "region": "punjab_haryana",
            "latitude": [30.1, 30.2, 30.3, 30.4],
            "longitude": [75.1, 75.2, 75.3, 75.4],
            "frp": [5.0, 6.0, 1.0, 2.0],
            "confidence": ["n", "h", "l", "n"],
            "daynight": "D",
            "source": "VIIRS_SNPP_SP",
            "version": "2",
            "time_utc": pd.to_datetime(
                ["2025-11-10 08:00", "2025-11-10 08:00", "2025-11-10 08:00", "2025-11-11 08:00"],
                utc=True,
            ),
        }
    )
    path = root / "fires" / "punjab_haryana" / "2025.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    fires.to_parquet(path, index=False)

    pd.DataFrame(
        {"location_id": [1, 2, 3, 4, 9], "name": [f"Station {i}" for i in (1, 2, 3, 4, 9)]}
    ).to_csv(root / "stations.csv", index=False)


if __name__ == "__main__":
    import sys

    make_raw(Path(sys.argv[1]))
