import numpy as np
import pandas as pd
import pytest

from breathe_check.analysis import deweather as dw
from breathe_check.analysis import indore as ind


def days(city, start, values, stations=3):
    dates = pd.date_range(start, periods=len(values), freq="D")
    return pd.DataFrame({"city": city, "date": dates, "pm25": values, "n_stations": stations})


def test_season_summary_counts_limits_and_skips_short_seasons():
    full = days("indore", "2025-07-01", [30.0] * 200 + [90.0] * 150)
    short = days("indore", "2024-11-01", [50.0] * 100)
    s = ind.season_summary(pd.concat([full, short]), ["indore"])
    assert s["season"].tolist() == ["2025-26"]  # the 100-day season is left out
    row = s.iloc[0]
    assert row["pm25"] == pytest.approx((30 * 200 + 90 * 150) / 350)
    assert row["days_over_india"] == 150
    assert row["days_over_who"] == 350
    assert row["times_who_guideline"] == pytest.approx(row["pm25"] / 5)


def test_band_shares_add_up_to_one():
    df = days("indore", "2025-07-01", [10.0, 45.0, 75.0, 100.0, 200.0, 300.0])
    b = ind.band_days(df, ["indore"], "2025-26").set_index("city")
    assert b.sum(axis=1).iloc[0] == pytest.approx(1.0)
    assert np.allclose(b.iloc[0].to_numpy(dtype=float), 1 / 6)


def test_same_station_trend_drops_flagged_days():
    flags = [
        "flag_impossible",
        "flag_incomplete",
        "flag_flat",
        "flag_repeated",
        "flag_city_outlier",
    ]
    rows = []
    for season_start, value in (("2019-07-01", 40.0), ("2025-07-01", 50.0)):
        for i, d in enumerate(pd.date_range(season_start, periods=10)):
            row = {"location_id": 1, "date": d, "pm25": value, **dict.fromkeys(flags, False)}
            if i == 0:
                row.update(pm25=900.0, flag_impossible=True)
            rows.append(row)
    out = ind.same_station(pd.DataFrame(rows), 1, ["2019-20", "2025-26"])
    assert out["pm25"].tolist() == [40.0, 50.0]
    assert out["change_pct"].iloc[1] == pytest.approx(25.0)


def test_weather_fair_spots_a_city_dirtier_than_its_weather():
    """Two cities share one weather-to-PM2.5 rule, but 'dirty' adds 50% on top."""
    rng = np.random.default_rng(0)
    frames = []
    for city, extra in (("clean", 1.0), ("dirty", 1.5)):
        dates = pd.date_range("2022-07-01", "2026-06-30", freq="D")
        wind = rng.gamma(2.0, 4.0, len(dates))
        pm = np.exp(4 - 0.06 * wind + rng.normal(0, 0.05, len(dates))) * extra
        df = pd.DataFrame({"city": city, "date": dates, "pm25": pm, "wind_kmh": wind})
        for col in dw.WEATHER:
            if col not in df:
                df[col] = rng.normal(0, 1, len(dates))
        frames.append(df)
    wf = ind.weather_fair(pd.concat(frames), "2025-26").set_index("city")
    # shared model lands in between, so 'clean' sits below 1 and 'dirty' above
    assert wf.loc["clean", "ratio"] < 1 < wf.loc["dirty", "ratio"]
    assert wf.loc["dirty", "ratio"] / wf.loc["clean", "ratio"] == pytest.approx(1.5, rel=0.1)
