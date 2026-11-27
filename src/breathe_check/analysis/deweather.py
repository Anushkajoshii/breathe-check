"""Weather-adjusted ("deweathered") PM2.5.

The idea, in plain words:
1. For each city, train a model that predicts the day's PM2.5 from weather and
   the calendar ONLY: wind, mixing height, rain, humidity, temperature, time of
   year, day of week, and yesterday's weather (pollution builds up over days).
2. The model never sees GRAP stages, crop fires, Diwali or the year. So its
   prediction is "what PM2.5 this weather usually brings, at this time of year".
3. Each day's ratio of actual to expected is what weather can't explain.
   Multiply it by the city's typical level to get a weather-adjusted value:
   what the day would have looked like in average weather.

To keep this honest, every day is predicted by a model that was trained
without that day's whole season (July to June). So the model can't simply
memorise a winter and then "explain" it.

This follows the approach of Grange and Carslaw (2019) and others, using a
gradient-boosted tree model (LightGBM) on the log of PM2.5.
"""

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

WEATHER = [
    "temp_c",
    "temp_min_c",
    "temp_max_c",
    "humidity_pct",
    "dew_point_c",
    "rain_mm",
    "pressure_hpa",
    "cloud_pct",
    "wind_kmh",
    "gust_max_kmh",
    "wind_u",
    "wind_v",
    "mixing_height_m",
    "mixing_height_min_m",
    "sun_kwh_m2",
]
LAGGED = ["wind_kmh", "mixing_height_m", "rain_mm", "temp_min_c", "humidity_pct"]
CALENDAR = ["doy_sin", "doy_cos", "weekday"]

PARAMS = {
    "n_estimators": 400,
    "learning_rate": 0.03,
    "num_leaves": 15,
    "min_child_samples": 20,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "verbose": -1,
    "random_state": 42,
}


def season_of(dates: pd.Series) -> pd.Series:
    """Label July 2021 to June 2022 as "2021-22", so a whole winter stays together."""
    d = pd.to_datetime(dates)
    start = np.where(d.dt.month >= 7, d.dt.year, d.dt.year - 1)
    return pd.Series([f"{y}-{str(y + 1)[-2:]}" for y in start], index=dates.index)


def add_features(city_day: pd.DataFrame) -> pd.DataFrame:
    """Add calendar features and yesterday's weather. Expects one city, or several."""
    df = city_day.sort_values(["city", "date"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    doy = df["date"].dt.day_of_year
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    df["weekday"] = df["date"].dt.dayofweek
    for col in LAGGED:
        prev = df.groupby("city")[col].shift(1)
        # only use yesterday's value if yesterday really is the day before
        gap = df.groupby("city")["date"].diff().dt.days
        df[f"{col}_yesterday"] = prev.where(gap == 1)
    df["season"] = season_of(df["date"])
    return df


def feature_names(use_weather: bool = True) -> list[str]:
    if not use_weather:
        return list(CALENDAR)
    return WEATHER + [f"{c}_yesterday" for c in LAGGED] + CALENDAR


@dataclass
class CityResult:
    city: str
    predictions: pd.DataFrame  # date, pm25, expected (out-of-season), season
    model: lgb.LGBMRegressor  # trained on all seasons, for explaining
    features: list[str]


def fit(X: pd.DataFrame, y: pd.Series, params: dict | None = None) -> lgb.LGBMRegressor:
    model = lgb.LGBMRegressor(**{**PARAMS, **(params or {})})
    model.fit(X, y)
    return model


def deweather_city(
    df: pd.DataFrame, use_weather: bool = True, params: dict | None = None
) -> CityResult:
    """Leave-one-season-out predictions of log PM2.5 for one city."""
    features = feature_names(use_weather)
    data = df[df["pm25"].notna() & (df["pm25"] > 0)].copy()
    data["log_pm25"] = np.log(data["pm25"])
    data["expected_log"] = np.nan
    seasons = sorted(data["season"].unique())
    for season in seasons:
        test = data["season"] == season
        if test.all():
            break
        model = fit(data.loc[~test, features], data.loc[~test, "log_pm25"], params)
        data.loc[test, "expected_log"] = model.predict(data.loc[test, features])
    final = fit(data[features], data["log_pm25"], params)
    out = data[["city", "date", "season", "pm25", "log_pm25", "expected_log"]].copy()
    out["expected"] = np.exp(out["expected_log"])
    return CityResult(str(data["city"].iloc[0]), out, final, features)


def score(predictions: pd.DataFrame) -> dict:
    """How well out-of-season predictions match reality."""
    p = predictions.dropna(subset=["expected_log"])
    resid = p["log_pm25"] - p["expected_log"]
    total = p["log_pm25"] - p["log_pm25"].mean()
    return {
        "days": len(p),
        "r2_log": 1 - (resid**2).sum() / (total**2).sum(),
        "median_abs_error_pct": float(np.median(np.abs(np.exp(resid) - 1)) * 100),
        "mae_ugm3": float(np.mean(np.abs(p["pm25"] - p["expected"]))),
    }


def weather_adjusted(predictions: pd.DataFrame) -> pd.DataFrame:
    """Turn out-of-season predictions into a weather-adjusted PM2.5 series.

    ratio = actual / expected. 1.0 means "exactly what the weather predicts";
    0.8 means 20% cleaner than this weather usually brings.
    pm25_adjusted = ratio x the city's typical expected level for that time of
    year, so it stays in ug/m3 and keeps the seasonal shape while removing
    day-to-day weather swings.
    """
    p = predictions.dropna(subset=["expected_log"]).copy()
    p["ratio"] = p["pm25"] / p["expected"]
    doy = pd.to_datetime(p["date"]).dt.day_of_year
    week = ((doy - 1) // 7).clip(upper=51)
    typical = p.groupby(week)["expected"].transform("median")
    p["pm25_adjusted"] = p["ratio"] * typical
    return p


def explain(result: CityResult, df: pd.DataFrame) -> pd.DataFrame:
    """Average size of each feature's push on the prediction (mean |SHAP|).

    LightGBM computes SHAP values directly (pred_contrib=True). Values are on
    the log scale: 0.1 means the feature typically moves PM2.5 by about 10%.
    """
    data = df[df["pm25"].notna() & (df["pm25"] > 0)]
    contrib = result.model.predict(data[result.features], pred_contrib=True)
    shap = pd.DataFrame(contrib[:, :-1], columns=result.features)
    return (
        shap.abs()
        .mean()
        .sort_values(ascending=False)
        .rename("mean_abs_shap")
        .rename_axis("feature")
        .reset_index()
    )
