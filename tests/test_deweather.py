"""Check the deweathering model on made-up data where we know the right answer."""

import numpy as np
import pandas as pd
import pytest

from breathe_check.analysis import deweather as dw


@pytest.fixture(scope="module")
def fake_city():
    """Six seasons of one city where PM2.5 depends on time of year and wind only,
    plus a 'policy' that cuts PM2.5 by 30% in one stretch the model never sees."""
    rng = np.random.default_rng(1)
    dates = pd.date_range("2019-07-01", "2025-06-30", freq="D")
    n = len(dates)
    wind = rng.gamma(2.0, 4.0, n)
    doy = dates.dayofyear.to_numpy()
    log_pm = 4.0 + 0.8 * np.cos(2 * np.pi * (doy - 15) / 365.25) - 0.05 * wind
    policy = (dates >= "2023-11-01") & (dates <= "2023-12-31")
    log_pm = log_pm + np.where(policy, np.log(0.7), 0) + rng.normal(0, 0.08, n)
    df = pd.DataFrame(
        {"city": "testville", "date": dates, "pm25": np.exp(log_pm), "wind_kmh": wind}
    )
    for col in dw.WEATHER:
        if col not in df:
            df[col] = rng.normal(0, 1, n)  # pure noise: should not matter
    return dw.add_features(df), policy


def test_season_runs_july_to_june():
    dates = pd.Series(pd.to_datetime(["2021-06-30", "2021-07-01", "2022-01-15"]))
    assert dw.season_of(dates).tolist() == ["2020-21", "2021-22", "2021-22"]


def test_yesterday_is_blank_after_a_missing_day():
    df = pd.DataFrame(
        {"city": "x", "date": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-05"])}
        | {c: [1.0, 2.0, 3.0] for c in dw.WEATHER}
    )
    out = dw.add_features(df)
    assert out["wind_kmh_yesterday"].tolist()[1] == 1.0
    assert np.isnan(out["wind_kmh_yesterday"].tolist()[2])


def test_model_learns_weather_and_beats_calendar_only(fake_city):
    df, _ = fake_city
    weather = dw.score(dw.deweather_city(df).predictions)
    calendar = dw.score(dw.deweather_city(df, use_weather=False).predictions)
    assert weather["r2_log"] > 0.8
    assert weather["r2_log"] > calendar["r2_log"] + 0.1


def test_every_day_is_predicted_by_a_model_that_never_saw_its_season(fake_city):
    df, _ = fake_city
    preds = dw.deweather_city(df).predictions
    assert preds["expected_log"].notna().all()


def test_weather_adjusted_reveals_the_hidden_policy_cut(fake_city):
    df, policy = fake_city
    adjusted = dw.weather_adjusted(dw.deweather_city(df).predictions)
    in_policy = adjusted["date"].between("2023-11-01", "2023-12-31")
    cut = adjusted.loc[in_policy, "ratio"].median()
    normal = adjusted.loc[~in_policy, "ratio"].median()
    # the true cut is 30%; the model only sees weather, so it should find most of it
    assert normal == pytest.approx(1.0, abs=0.05)
    assert 0.6 < cut < 0.8


def test_wind_is_the_top_weather_input(fake_city):
    df, _ = fake_city
    result = dw.deweather_city(df)
    importance = dw.explain(result, df)
    weather_only = importance[~importance["feature"].isin(dw.CALENDAR)]
    assert weather_only.iloc[0]["feature"] == "wind_kmh"
