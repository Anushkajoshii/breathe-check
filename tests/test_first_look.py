import numpy as np
import pandas as pd
import pytest

from breathe_check.analysis import first_look as fl


def city_day(rows):
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    return df


def test_station_coverage_fills_missing_months_with_zero():
    df = city_day(
        [
            {"city": "delhi", "city_role": "grap", "date": "2022-01-01", "n_stations": 4},
            {"city": "noida", "city_role": "grap", "date": "2022-01-01", "n_stations": 2},
            {"city": "delhi", "city_role": "grap", "date": "2022-03-01", "n_stations": 5},
        ]
    )
    table = fl.station_coverage(df)
    assert table["n_stations"].tolist() == [6, 0, 5]


def test_monthly_profile_averages_by_city_and_month():
    df = city_day(
        [
            {"city": "delhi", "date": "2021-11-01", "pm25": 200.0},
            {"city": "delhi", "date": "2025-11-01", "pm25": 100.0},
            {"city": "indore", "date": "2025-11-01", "pm25": 60.0},
            {"city": "pune", "date": "2025-11-01", "pm25": 40.0},
        ]
    )
    table = fl.monthly_profile(df, ["delhi", "indore"])
    assert table.set_index("city")["pm25"].to_dict() == {"delhi": 150.0, "indore": 60.0}


def test_diwali_jump_compares_day_after_with_week_before():
    days = range(-10, 11)
    window = pd.DataFrame(
        {
            "city": "delhi",
            "days_from_diwali": list(days),
            "pm25": [100.0] * 11 + [300.0] + [100.0] * 9,
            "years": 1,
        }
    )
    jump = fl.diwali_jump(window).iloc[0]
    assert jump["day_after"] == 300
    assert jump["ratio"] == pytest.approx(3.0)


def test_north_west_wind_is_270_to_360_degrees():
    df = city_day(
        [
            {
                "city": "delhi",
                "date": "2025-11-01",
                "pm25": 300.0,
                "fires_confident_yesterday": 2000,
                "wind_from_deg": 300,
            },
            {
                "city": "delhi",
                "date": "2025-11-02",
                "pm25": 200.0,
                "fires_confident_yesterday": 2000,
                "wind_from_deg": 90,
            },
            {
                "city": "delhi",
                "date": "2025-10-01",
                "pm25": 999.0,
                "fires_confident_yesterday": 2000,
                "wind_from_deg": 300,
            },
        ]
    )
    table = fl.fires_and_wind(df).dropna()
    got = table.set_index("wind")["pm25"].to_dict()
    # 1 October is outside the 15 Oct - 30 Nov window and is left out
    assert got == {"Other winds": 200.0, "Wind from the north-west": 300.0}


def test_mixing_height_groups_are_equal_sized():
    rng = np.random.default_rng(0)
    df = city_day(
        [
            {"city": "delhi", "date": f"2025-12-{d:02d}", "pm25": 100.0, "mixing_height_m": h}
            for d, h in zip(range(1, 31), rng.uniform(100, 600, 30), strict=True)
        ]
    )
    table = fl.mixing_height_effect(df, bins=3)
    assert table["days"].tolist() == [10, 10, 10]
    assert table["mixing_m"].is_monotonic_increasing
