"""Make the Part 5 charts and print the numbers quoted in reports/01-first-look.md.

uv run python analysis/first_look.py
"""

from breathe_check.analysis import first_look as fl
from breathe_check.analysis import style
from breathe_check.analysis.load import load

TRIO = ["delhi", "indore", "bengaluru"]


def main() -> None:
    style.setup()
    city_day = load("city_day")
    city_hour = load("city_hour", "city in ('delhi', 'indore', 'bengaluru')")

    coverage = fl.station_coverage(city_day)
    print(style.save(fl.plot_station_coverage(coverage), "01_station_coverage"))

    monthly = fl.monthly_profile(city_day, TRIO)
    print(style.save(fl.plot_monthly_profile(monthly, TRIO), "02_monthly_profile"))
    print(monthly.pivot(index="month", columns="city", values="pm25").round(0).to_string())

    hourly = fl.hourly_profile(city_hour, TRIO)
    print(style.save(fl.plot_hourly_profile(hourly, TRIO), "03_hourly_profile"))
    h = hourly.pivot_table(index=["season", "city"], columns="hour", values="pm25")
    print(h.agg(["idxmin", "min", "idxmax", "max"], axis=1).round(0).to_string())

    window = fl.diwali_window(city_day, TRIO)
    print(style.save(fl.plot_diwali(window, TRIO), "04_diwali"))
    print(fl.diwali_jump(window).round(2).to_string())

    fires = fl.fires_and_wind(city_day)
    print(style.save(fl.plot_fires_and_wind(fires), "05_fires_and_wind"))
    print(fires.round(0).to_string())

    mixing = fl.mixing_height_effect(city_day)
    print(style.save(fl.plot_mixing_height(mixing), "06_mixing_height"))
    print(mixing.round(0).to_string())


if __name__ == "__main__":
    main()
