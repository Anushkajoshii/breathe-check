"""Part 8: Indore vs India's limits, the WHO guideline and its neighbours.

uv run python analysis/indore.py
"""

import duckdb

from breathe_check import settings
from breathe_check.analysis import indore as ind
from breathe_check.analysis import indore_charts as charts
from breathe_check.analysis import style
from breathe_check.analysis.load import load

SEASON = "2025-26"
PITHAMPUR = 5603


def main() -> None:
    style.setup()
    city_day = load("city_day")
    cities = ind.PEERS + ind.CONTEXT
    summary = ind.season_summary(city_day, cities)
    print(summary.round(2).to_string(index=False))

    bands = ind.band_days(city_day, cities, SEASON)
    print(bands.round(2).to_string(index=False))
    print(ind.winter_vs_rest(city_day, cities, SEASON).round(0).to_string(index=False))

    db = settings.DATA_DIR / "breathe.duckdb"
    if db.exists():
        flagged = (
            duckdb.connect(str(db), read_only=True)
            .execute(f"select * from int_air_daily_flagged where location_id = {PITHAMPUR}")
            .df()
        )
        print(
            ind.same_station(flagged, PITHAMPUR, ["2019-20", SEASON])
            .round(1)
            .to_string(index=False)
        )

    fair = ind.weather_fair(city_day, SEASON)
    print(fair.round(2).to_string(index=False))

    out = settings.DATA_DIR / "clean"
    summary.to_parquet(out / "city_season_summary.parquet", index=False)
    fair.to_parquet(out / "weather_fair_ranking.parquet", index=False)

    order = summary[summary["season"] == SEASON].sort_values("pm25")["city"].tolist()
    print(style.save(charts.plot_yearly(summary, SEASON), "13_indore_yearly"))
    print(style.save(charts.plot_bands(bands, order), "14_indore_aqi_days"))
    print(style.save(charts.plot_weather_fair(fair), "15_weather_fair_ranking"))


if __name__ == "__main__":
    main()
