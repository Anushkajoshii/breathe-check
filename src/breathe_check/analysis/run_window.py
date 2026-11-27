"""Part 9: "When is the safest time to run outside tomorrow?"

For every hour of tomorrow, three numbers: a low, a middle and a high PM2.5.
They come from three LightGBM models trained for the 10th, 50th and 90th
percentile ("quantile regression"). If the models are honest, the real value
lands below "low" about 10% of the time and above "high" about 10% of the time,
so the low-to-high range holds it about 80% of the time.

What the models use, all known by the evening before:
- tomorrow's weather forecast for each hour (wind, mixing height, rain, ...)
- the hour, the time of year, the day of the week, and which city
- how polluted today was from midnight to 6 pm (pollution carries over)

Then the "best window": the 2 back-to-back hours between 5 am and 10 pm with the
lowest middle forecast.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd

from breathe_check.standards import PM25_PER_CIGARETTE, aqi_band

WEATHER = [
    "temp_c",
    "humidity_pct",
    "dew_point_c",
    "rain_mm",
    "pressure_hpa",
    "cloud_pct",
    "wind_kmh",
    "gust_kmh",
    "mixing_height_m",
    "sun_wm2",
    "wind_u",
    "wind_v",
]
FEATURES = [
    *WEATHER,
    "hour",
    "doy_sin",
    "doy_cos",
    "weekday",
    "city",
    "pm_today_to_6pm",
    "pm_today_5pm",
]
TARGET_COVERAGE = 0.8
QUANTILES = {"low": 0.1, "mid": 0.5, "high": 0.9}
FIRST_START, LAST_START = 5, 20  # windows start 5 am to 8 pm, so they end by 10 pm

PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.04,
    "num_leaves": 31,
    "min_child_samples": 40,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "verbose": -1,
    "random_state": 7,
}


def add_wind_parts(df: pd.DataFrame) -> pd.DataFrame:
    rad = np.radians(df["wind_dir_deg"])
    df["wind_u"] = -df["wind_kmh"] * np.sin(rad)
    df["wind_v"] = -df["wind_kmh"] * np.cos(rad)
    return df


def today_to_6pm(city_hour: pd.DataFrame) -> pd.DataFrame:
    """For each city and day: average PM2.5 from midnight to 6 pm, and the 5 pm reading
    (the freshest one in hand when the forecast goes out in the evening)."""
    h = city_hour[city_hour["hour"] < 18].copy()
    h["date"] = pd.to_datetime(h["time_ist"]).dt.normalize()
    mean = h.groupby(["city", "date"], as_index=False)["pm25"].mean()
    mean = mean.rename(columns={"pm25": "pm_today_to_6pm"})
    five = h[h["hour"] == 17][["city", "date", "pm25"]].rename(columns={"pm25": "pm_today_5pm"})
    return mean.merge(five, on=["city", "date"], how="left")


def build_rows(city_hour: pd.DataFrame) -> pd.DataFrame:
    """One row per city per hour, with the previous day's midnight-to-6pm level attached."""
    df = add_wind_parts(city_hour.copy())
    df["time_ist"] = pd.to_datetime(df["time_ist"])
    df["date"] = df["time_ist"].dt.normalize()
    doy = df["time_ist"].dt.day_of_year
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    df["weekday"] = df["time_ist"].dt.dayofweek
    prev = today_to_6pm(city_hour)
    prev["date"] = prev["date"] + pd.Timedelta(days=1)  # yesterday's level, for today's rows
    df = df.merge(prev, on=["city", "date"], how="left")
    df["city"] = df["city"].astype("category")
    return df


def train(rows: pd.DataFrame) -> dict[str, lgb.LGBMRegressor]:
    data = rows.dropna(subset=["pm25", "pm_today_to_6pm"])
    data = data[data["pm25"] > 0]
    y = np.log(data["pm25"])
    models = {}
    for name, alpha in QUANTILES.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **PARAMS)
        m.fit(data[FEATURES], y)
        models[name] = m
    return models


def predict(models: dict, rows: pd.DataFrame, widen: float = 1.0) -> pd.DataFrame:
    """Low, middle and high forecast. `widen` stretches the range around the middle
    (on the log scale) so it holds the real value as often as promised."""
    out = rows.copy()
    logs = {name: m.predict(rows[FEATURES]) for name, m in models.items()}
    ordered = np.sort(np.column_stack([logs["low"], logs["mid"], logs["high"]]), axis=1)
    low, mid, high = ordered[:, 0], ordered[:, 1], ordered[:, 2]
    out["low"] = np.exp(mid - widen * (mid - low))
    out["mid"] = np.exp(mid)
    out["high"] = np.exp(mid + widen * (high - mid))
    return out


def coverage(pred: pd.DataFrame) -> float:
    p = pred.dropna(subset=["pm25"])
    return float(((p["pm25"] >= p["low"]) & (p["pm25"] <= p["high"])).mean())


def fit_with_calibration(rows: pd.DataFrame, holdout_days: int = 60) -> tuple[dict, float]:
    """Train on all but the last `holdout_days`, find how much to widen the range so it
    holds 80% of real values there, then retrain on everything and keep that widening."""
    cut = rows["time_ist"].max() - pd.Timedelta(days=holdout_days)
    first = train(rows[rows["time_ist"] < cut])
    held = rows[rows["time_ist"] >= cut].dropna(subset=["pm25", "pm_today_to_6pm"])
    widen = 1.0
    for w in np.arange(1.0, 2.01, 0.05):
        if coverage(predict(first, held, w)) >= TARGET_COVERAGE:
            widen = float(w)
            break
    else:
        widen = 2.0
    return train(rows), widen


def best_window(day: pd.DataFrame, value: str = "mid") -> dict | None:
    """The 2 back-to-back hours (5 am to 10 pm) with the lowest `value`."""
    d = day.set_index("hour")[value]
    best = None
    for start in range(FIRST_START, LAST_START + 1):
        if start in d.index and start + 1 in d.index:
            mean = (d[start] + d[start + 1]) / 2
            if best is None or mean < best[1]:
                best = (start, mean)
    if best is None:
        return None
    return {"start": best[0], "end": best[0] + 2, "pm25": float(best[1])}


def window_means(day: pd.DataFrame, value: str = "pm25") -> pd.Series:
    """Average of `value` for every 2-hour window, indexed by start hour."""
    d = day.set_index("hour")[value]
    out = {}
    for start in range(FIRST_START, LAST_START + 1):
        if start in d.index and start + 1 in d.index:
            out[start] = (d[start] + d[start + 1]) / 2
    return pd.Series(out, dtype=float)


def evaluate(pred: pd.DataFrame, train_rows: pd.DataFrame) -> dict:
    """How the forecast did on days it never saw, against two simple rules of thumb."""
    p = pred.dropna(subset=["pm25", "pm_today_to_6pm"]).copy()
    # rule of thumb 1: tomorrow at every hour = today's midnight-6pm average
    p["persistence"] = p["pm_today_to_6pm"]
    # rule of thumb 2: the usual level for this city, hour and month in the training data
    t = train_rows.dropna(subset=["pm25"]).copy()
    t["month"] = t["time_ist"].dt.month
    usual = t.groupby(["city", "month", "hour"], observed=True)["pm25"].mean().rename("usual")
    p["month"] = p["time_ist"].dt.month
    p = p.join(usual, on=["city", "month", "hour"])
    by_hour = t.groupby(["city", "hour"], observed=True)["pm25"].mean().rename("usual_hour")
    p = p.join(by_hour, on=["city", "hour"])
    p["usual"] = p["usual"].fillna(p["usual_hour"])

    def mae(col):
        return float(np.mean(np.abs(p[col] - p["pm25"])))

    result = {
        "hours_tested": len(p),
        "mae_forecast": mae("mid"),
        "mae_today_level": mae("persistence"),
        "mae_usual_for_hour": mae("usual"),
        "in_range": float(((p["pm25"] >= p["low"]) & (p["pm25"] <= p["high"])).mean()),
        "below_low": float((p["pm25"] < p["low"]).mean()),
        "above_high": float((p["pm25"] > p["high"]).mean()),
    }

    # best-window checks, one per city-day with enough real hours
    hits, fixed_hits, saved, days = 0, 0, [], 0
    for _, day in p.groupby(["city", "date"], observed=True):
        actual = window_means(day, "pm25")
        if len(actual) < 12:
            continue
        chosen = best_window(day, "mid")
        if chosen is None or chosen["start"] not in actual.index:
            continue
        days += 1
        cleanest_third = actual.quantile(1 / 3)
        hits += actual[chosen["start"]] <= cleanest_third
        if 14 in actual.index:
            fixed_hits += actual[14] <= cleanest_third
        if 7 in actual.index:  # the common 7-9 am run
            saved.append(1 - actual[chosen["start"]] / actual[7])
    result.update(
        {
            "days_tested": days,
            "best_window_in_cleanest_third": hits / days if days else np.nan,
            "always_2_to_4pm_in_cleanest_third": fixed_hits / days if days else np.nan,
            "median_cut_vs_7_to_9am": float(np.median(saved)) if saved else np.nan,
        }
    )
    return result


# ---------- the small cards ----------


def cigarette_card(pm25_mean: float) -> dict:
    band = aqi_band(max(pm25_mean, 0))
    return {
        "pm25": round(float(pm25_mean), 1),
        "cigarettes": round(float(pm25_mean) / PM25_PER_CIGARETTE, 1),
        "aqi_category": band.name,
        "advice": band.advice,
    }


SMOKE_MONTHS = (10, 11)


def smoke_check(
    fires_yesterday: int, nw_wind_share: float, month: int, fires_date: str = "yesterday"
) -> dict:
    """Is crop-fire smoke from Punjab and Haryana likely to reach Delhi-NCR today?

    "Likely" when more than 1,500 confident fires were seen yesterday AND the wind
    blows from the north-west (where the fields are) for at least half of today's
    hours. Checked on Delhi's October-November days, 2018-2026: on "Likely" days
    Delhi averaged 252 ug/m3 and was 14% dirtier than its weather predicts; on all
    other days it averaged 143 and was right in line with its weather. A middle
    "Possible" level was tried and showed no difference, so it was dropped.
    """
    if month not in SMOKE_MONTHS:
        return {
            "level": "Not burning season",
            "why": "Crop burning happens mainly in October and November.",
        }
    likely = fires_yesterday > 1500 and nw_wind_share >= 0.5
    why = (
        f"{fires_yesterday:,} fires seen in Punjab and Haryana {fires_date}; wind from the "
        f"north-west for {nw_wind_share:.0%} of the forecast hours."
    )
    return {"level": "Likely" if likely else "Unlikely", "why": why}
