import numpy as np
import pandas as pd
import pytest

from breathe_check.analysis import run_window as rw
from breathe_check.cities import get_city
from breathe_check.forecast import city_payload


def day(values):
    return pd.DataFrame({"hour": range(len(values)), "mid": values, "pm25": values})


def test_best_window_is_the_cleanest_two_hours_between_5am_and_10pm():
    values = [5.0] * 5 + [50.0] * 19  # the clean hours are before 5 am, so not allowed
    values[15], values[16] = 20.0, 22.0
    assert rw.best_window(day(values)) == {"start": 15, "end": 17, "pm25": 21.0}


def test_best_window_ends_by_10pm():
    values = [50.0] * 24
    values[22], values[23] = 1.0, 1.0  # cleanest, but too late
    assert rw.best_window(day(values))["start"] <= rw.LAST_START


def test_today_to_6pm_uses_only_hours_before_6pm_and_the_5pm_reading():
    hours = pd.DataFrame(
        {
            "city": "indore",
            "time_ist": pd.date_range("2026-11-01", periods=24, freq="h"),
            "hour": range(24),
            "pm25": [10.0] * 18 + [100.0] * 6,
        }
    )
    hours.loc[17, "pm25"] = 28.0
    out = rw.today_to_6pm(hours).iloc[0]
    assert out["pm_today_to_6pm"] == pytest.approx((10 * 17 + 28) / 18)
    assert out["pm_today_5pm"] == 28.0


def test_widening_stretches_the_range_around_the_middle():
    class Fixed:
        def __init__(self, v):
            self.v = v

        def predict(self, X):
            return np.full(len(X), self.v)

    models = {"low": Fixed(np.log(20)), "mid": Fixed(np.log(40)), "high": Fixed(np.log(80))}
    rows = pd.DataFrame({f: [0.0] for f in rw.FEATURES})
    plain = rw.predict(models, rows, 1.0).iloc[0]
    wide = rw.predict(models, rows, 1.5).iloc[0]
    assert (plain["low"], plain["mid"], plain["high"]) == pytest.approx((20, 40, 80))
    assert wide["mid"] == pytest.approx(40)
    assert wide["low"] < 20 and wide["high"] > 80


def test_crossed_quantiles_are_put_back_in_order():
    class Fixed:
        def __init__(self, v):
            self.v = v

        def predict(self, X):
            return np.full(len(X), self.v)

    models = {"low": Fixed(np.log(60)), "mid": Fixed(np.log(40)), "high": Fixed(np.log(30))}
    row = rw.predict(models, pd.DataFrame({f: [0.0] for f in rw.FEATURES})).iloc[0]
    assert row["low"] <= row["mid"] <= row["high"]


def test_smoke_check_levels():
    assert rw.smoke_check(2000, 0.6, 11)["level"] == "Likely"
    assert rw.smoke_check(2000, 0.2, 11)["level"] == "Unlikely"  # wind from elsewhere
    assert rw.smoke_check(300, 0.9, 11)["level"] == "Unlikely"  # few fires
    assert rw.smoke_check(5000, 1.0, 6)["level"] == "Not burning season"


def test_cigarette_card():
    card = rw.cigarette_card(44.0)
    assert card["cigarettes"] == 2.0
    assert card["aqi_category"] == "Satisfactory"


def test_city_payload_shape():
    hours = pd.DataFrame(
        {
            "hour": range(24),
            "time_ist": pd.date_range("2026-11-29", periods=24, freq="h"),
            "low": 20.0,
            "mid": [40.0] * 12 + [25.0, 24.0] + [40.0] * 10,
            "high": 70.0,
        }
    )
    level = pd.Series({"level_from": pd.Timestamp("2026-11-28")})
    p = city_payload(get_city("indore"), hours, level, 41.8, None, {})
    assert p["for_date"] == "2026-11-29"
    assert p["best_window"]["start"] == 12 and p["best_window"]["end"] == 14
    assert len(p["hours"]) == 24
    assert p["today"]["cigarettes"] == 1.9
    assert p["based_on_air_up_to"] == "2026-11-28"
