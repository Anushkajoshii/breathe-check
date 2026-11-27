"""Run the real dbt cleaning project on planted data and check every rule."""

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest
from planted_data import make_raw

ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR: dict[str, Path] = {}


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cleaning")
    make_raw(tmp / "raw")
    (tmp / "clean").mkdir()
    variables = json.dumps({"raw_dir": str(tmp / "raw"), "clean_dir": str(tmp / "clean")})
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dbt.cli.main",
            "build",
            "--project-dir",
            "transform",
            "--profiles-dir",
            "transform",
            "--vars",
            variables,
            "--target-path",
            str(tmp / "target"),
        ],
        cwd=ROOT,
        env={**os.environ, "BREATHE_DUCKDB": str(tmp / "test.duckdb")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    con = duckdb.connect(str(tmp / "test.duckdb"), read_only=True)
    CLEAN_DIR["path"] = tmp / "clean"
    yield con
    con.close()


def flagged_days(db, flag, location_id=4):
    rows = db.execute(
        f"select strftime(date, '%m-%d') from int_air_daily_flagged "
        f"where location_id = {location_id} and {flag} order by date"
    ).fetchall()
    return [r[0] for r in rows]


def test_impossible_value_is_caught(db):
    assert flagged_days(db, "flag_impossible") == ["11-08"]


def test_incomplete_day_is_caught(db):
    assert flagged_days(db, "flag_incomplete") == ["11-09"]


def test_flat_day_is_caught(db):
    assert flagged_days(db, "flag_flat") == ["11-10"]


def test_every_day_of_a_repeat_run_is_caught(db):
    assert flagged_days(db, "flag_repeated") == ["11-11", "11-12", "11-13"]


def test_station_far_above_its_city_is_caught(db):
    assert flagged_days(db, "flag_city_outlier") == ["11-15"]


def test_healthy_stations_are_never_flagged(db):
    n = db.execute(
        "select count(*) from int_air_daily_flagged where location_id in (1, 2, 3, 9) and "
        "(flag_impossible or flag_incomplete or flag_flat or flag_repeated or flag_city_outlier)"
    ).fetchone()[0]
    # station 3 starts with two equal days, which is fine: the rule needs three
    assert n == 0


def test_city_average_leaves_out_flagged_stations(db):
    row = db.execute(
        "select pm25, n_stations from city_day where city = 'delhi' and date = '2025-11-08'"
    ).fetchone()
    assert row[1] == 3
    assert row[0] == pytest.approx((102 + 112 + 106) / 3)


def hours_flagged(db, flag):
    rows = db.execute(
        f"select strftime(time_ist, '%d %H') from int_air_hourly_flagged where {flag} order by 1"
    ).fetchall()
    return [r[0] for r in rows]


def test_six_stuck_hours_are_all_caught(db):
    assert hours_flagged(db, "flag_stuck") == [f"06 {h:02d}" for h in range(10, 16)]


def test_hourly_spike_is_caught(db):
    # 07 20 is the planted 1200 reading: impossible and a spike, so both rules catch it
    assert hours_flagged(db, "flag_spike") == ["07 06", "07 20"]


def test_hourly_impossible_and_incomplete(db):
    assert hours_flagged(db, "flag_impossible") == ["07 20"]
    assert hours_flagged(db, "flag_incomplete") == ["07 16"]


def test_grap_stage_changes_on_the_order_date(db):
    rows = db.execute(
        "select strftime(date, '%m-%d'), grap_stage from city_day "
        "where city = 'delhi' and date between '2025-11-10' and '2025-11-11' order by date"
    ).fetchall()
    assert rows == [("11-10", 2), ("11-11", 3)]


def test_grap_is_zero_outside_ncr(db):
    assert (
        db.execute("select max(grap_stage) from city_day where city = 'indore'").fetchone()[0] == 0
    )


def test_days_from_diwali(db):
    # Diwali 2025 was 20 October
    value = db.execute(
        "select days_from_diwali from city_day where city = 'delhi' and date = '2025-11-06'"
    ).fetchone()[0]
    assert value == 17


def test_fire_counts_skip_low_confidence(db):
    row = db.execute(
        "select fires, fires_confident, fires_confident_yesterday from city_day "
        "where city = 'delhi' and date = '2025-11-11'"
    ).fetchone()
    assert row == (1, 1, 2)


def test_north_west_wind_direction(db):
    value = db.execute(
        "select wind_from_deg from city_day where city = 'delhi' and date = '2025-11-08'"
    ).fetchone()[0]
    assert value == pytest.approx(315)


def test_weather_lines_up_with_air_hours(db):
    missing = db.execute("select count(*) from city_hour where temp_c is null").fetchone()[0]
    assert missing == 0


def test_cleaned_tables_are_written_as_parquet(db):
    written = sorted(p.name for p in CLEAN_DIR["path"].glob("*.parquet"))
    assert written == [
        "city_day.parquet",
        "city_hour.parquet",
        "quality_report.parquet",
        "station_quality.parquet",
    ]
