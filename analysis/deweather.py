"""Part 6: train the weather-only models, test them, and save weather-adjusted PM2.5.

uv run python analysis/deweather.py
"""

import pandas as pd

from breathe_check import settings
from breathe_check.analysis import deweather as dw
from breathe_check.analysis import deweather_charts as charts
from breathe_check.analysis import style
from breathe_check.analysis.load import load


def main() -> None:
    style.setup()
    city_day = dw.add_features(load("city_day"))
    scores, adjusted, results = [], [], {}
    for city, part in city_day.groupby("city"):
        weather = dw.deweather_city(part)
        calendar = dw.deweather_city(part, use_weather=False)
        results[city] = (weather, part)
        s_w, s_c = dw.score(weather.predictions), dw.score(calendar.predictions)
        scores.append(
            {
                "city": city,
                "days": s_w["days"],
                "r2_weather": s_w["r2_log"],
                "r2_calendar_only": s_c["r2_log"],
                "typical_error_pct": s_w["median_abs_error_pct"],
                "typical_error_pct_calendar_only": s_c["median_abs_error_pct"],
            }
        )
        adjusted.append(dw.weather_adjusted(weather.predictions))
        print(f"{city:11s} R2 weather {s_w['r2_log']:.2f}  calendar-only {s_c['r2_log']:.2f}")

    scores = pd.DataFrame(scores).sort_values("r2_weather", ascending=False)
    adjusted = pd.concat(adjusted, ignore_index=True)

    out = settings.DATA_DIR / "clean"
    cols = ["city", "date", "season", "pm25", "expected", "ratio", "pm25_adjusted"]
    adjusted[cols].to_parquet(out / "city_day_adjusted.parquet", index=False)
    scores.to_parquet(out / "deweather_scores.parquet", index=False)
    print(scores.round(2).to_string(index=False))

    delhi_model, delhi_data = results["delhi"]
    importance = dw.explain(delhi_model, delhi_data)
    print(importance.head(10).round(3).to_string(index=False))

    print(style.save(charts.plot_scores(scores), "07_model_scores"))
    print(style.save(charts.plot_importance(importance), "08_what_drives_delhi"))
    delhi = adjusted[adjusted["city"] == "delhi"]
    print(
        style.save(charts.plot_actual_vs_expected(delhi, "2025-26"), "09_delhi_actual_vs_expected")
    )


if __name__ == "__main__":
    main()
