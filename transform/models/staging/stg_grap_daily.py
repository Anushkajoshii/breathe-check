"""Highest revised-GRAP stage in force on each day, from reference/grap_orders.csv.

Two versions: all orders, and leaving out rows marked needs_review, so the
analysis can show whether the unclear rows change anything.
"""

from pathlib import Path

from breathe_check import grap


def model(dbt, session):
    dbt.config(materialized="table")
    path = Path(dbt.config.get("reference_dir", "reference")) / "grap_orders.csv"
    orders = grap.load_orders(path)
    every = grap.daily_stage(orders)
    sure = grap.daily_stage(orders[orders["needs_review"] == "no"].reset_index(drop=True))
    every["grap_stage_sure_only"] = (
        sure.set_index("date").reindex(every["date"])["grap_stage"].values
    )
    every["date"] = every["date"].dt.date
    return every
