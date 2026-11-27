"""GRAP (Graded Response Action Plan) dates: when each pollution-rule stage was on.

Revised GRAP (from October 2022) has four stages, each adding stricter rules:
    Stage I   "Poor" air (AQI 201-300)
    Stage II  "Very Poor" (301-400)
    Stage III "Severe" (401-450)
    Stage IV  "Severe+" (above 450)

Stages stack: when Stage III is on, Stages I and II are on too. So on any day we
only need one number, the highest stage in force (0 means none).

The original GRAP (2017 to 2022) had no day-by-day record of stages, so for
those winters we only know the season window (15 October to 15 March).
"""

from pathlib import Path

import pandas as pd

from breathe_check.settings import ROOT

REFERENCE = ROOT / "reference"


def load_orders(path: Path | None = None) -> pd.DataFrame:
    orders = pd.read_csv(path or REFERENCE / "grap_orders.csv", parse_dates=["order_date"])
    return orders


def check_orders(orders: pd.DataFrame) -> list[str]:
    """Return a list of problems with the orders file. Empty means it looks right."""
    problems = []
    if not orders["order_date"].is_monotonic_increasing:
        problems.append("orders are not in date order")
    bad_action = ~orders["action"].isin(["invoke", "revoke"])
    problems += [f"row {i}: unknown action" for i in orders.index[bad_action]]
    bad_stage = ~orders["stage"].isin([1, 2, 3, 4])
    problems += [f"row {i}: stage must be 1-4" for i in orders.index[bad_stage]]
    if orders["source_url"].isna().any() or not orders["source_url"].str.startswith("http").all():
        problems.append("every order needs a source link")
    level = 0
    for _, row in orders.iterrows():
        if row["action"] == "revoke" and level < row["stage"]:
            problems.append(
                f"{row['order_date']:%Y-%m-%d}: revokes stage {row['stage']} "
                f"but only stage {level} was on"
            )
        level = apply(level, row["action"], row["stage"])
    return problems


def apply(level: int, action: str, stage: int) -> int:
    """New highest stage after one order."""
    if action == "invoke":
        return max(level, stage)
    return min(level, stage - 1)


def daily_stage(orders: pd.DataFrame | None = None, end: str | None = None) -> pd.DataFrame:
    """One row per day from the first order: the highest GRAP stage in force.

    An order counts from the day it was issued. Orders usually say "with
    immediate effect", but they are often issued in the afternoon, so the
    analysis also tries counting from the next day.
    """
    orders = load_orders() if orders is None else orders
    last = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()
    days = pd.date_range(orders["order_date"].min(), last, freq="D")
    by_day = {d: list(g.itertuples()) for d, g in orders.groupby("order_date")}
    level, levels = 0, []
    for day in days:
        for row in by_day.get(day, []):
            level = apply(level, row.action, row.stage)
        levels.append(level)
    return pd.DataFrame({"date": days, "grap_stage": levels})


def load_original_seasons(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(
        path or REFERENCE / "grap_original_seasons.csv", parse_dates=["start", "end"]
    )


def load_diwali(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or REFERENCE / "diwali.csv", parse_dates=["date"])
