"""Part 9: test the run-window forecast on months it never saw, and draw the charts.

uv run python analysis/run_window.py
"""

import json

import pandas as pd

from breathe_check import settings
from breathe_check.analysis import run_window as rw
from breathe_check.analysis import run_window_charts as charts
from breathe_check.analysis import style
from breathe_check.analysis.load import load

TEST_FROM = pd.Timestamp("2026-06-01")
WINTER_FROM = pd.Timestamp("2026-10-15")


def main() -> None:
    style.setup()
    rows = rw.build_rows(load("city_hour"))
    train, test = rows[rows["time_ist"] < TEST_FROM], rows[rows["time_ist"] >= TEST_FROM]
    models, widen = rw.fit_with_calibration(train)
    pred = rw.predict(models, test, widen)

    overall = rw.evaluate(pred, train)
    winter = rw.evaluate(pred[pred["time_ist"] >= WINTER_FROM], train)
    print(f"range widening: {widen:.2f}")
    table = pd.DataFrame({"June to November 2026": overall, "15 Oct to 26 Nov 2026": winter})
    print(table.round(3).to_string())
    table.to_csv(settings.ROOT / "reports" / "run_window_test.csv")

    p = pred.dropna(subset=["pm25"]).copy()
    p["month"] = p["time_ist"].dt.month
    by_month = p.groupby("month").apply(
        lambda d: pd.Series(
            {
                "typical_miss": (d["mid"] - d["pm25"]).abs().mean(),
                "in_range": ((d["pm25"] >= d["low"]) & (d["pm25"] <= d["high"])).mean(),
            }
        ),
        include_groups=False,
    )
    print(by_month.round(2).to_string())

    print(style.save(charts.plot_window_test(overall), "17_run_window_test"))
    forecast = settings.DATA_DIR / "public" / "forecast" / "indore.json"
    if forecast.exists():
        print(
            style.save(charts.plot_tomorrow(json.loads(forecast.read_text())), "16_indore_tomorrow")
        )


if __name__ == "__main__":
    main()
