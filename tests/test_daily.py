import json

import pytest

from breathe_check import daily, settings


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(daily.storage, "pull_from_hub", lambda: calls.append("pull"))
    monkeypatch.setattr(daily.storage, "upload_to_hub", lambda **k: calls.append("upload"))
    monkeypatch.setattr(daily, "freshness", lambda: {"air_hourly_latest": "2026-11-27 23:00"})
    return tmp_path, calls


def status(tmp_path):
    return json.loads((tmp_path / "public" / "status.json").read_text())


def test_a_failed_source_is_recorded_but_the_rest_still_runs(sandbox, monkeypatch):
    tmp_path, calls = sandbox

    def fetch(step):
        if step[0] == "fires":
            raise ConnectionError("FIRMS is down")
        calls.append(step[0])

    monkeypatch.setattr(daily, "fetch", fetch)
    monkeypatch.setattr(daily, "clean", lambda: calls.append("clean"))
    monkeypatch.setattr(daily.forecast, "main", lambda: calls.append("forecast"))

    assert daily.main([]) == 0
    s = status(tmp_path)
    assert s["steps"]["fetch_fires"].startswith("failed: ConnectionError")
    assert s["steps"]["forecast"] == "ok"
    assert s["ok"] is False  # something failed, and the status says so
    assert calls[-1] == "upload"  # the forecast still goes out


def test_if_cleaning_fails_nothing_is_uploaded(sandbox, monkeypatch):
    tmp_path, calls = sandbox
    monkeypatch.setattr(daily, "fetch", lambda step: None)

    def broken():
        raise RuntimeError("dbt build failed")

    monkeypatch.setattr(daily, "clean", broken)
    monkeypatch.setattr(daily.forecast, "main", lambda: calls.append("forecast"))
    assert daily.main([]) == 1
    assert "forecast" not in calls and "upload" not in calls
    assert status(tmp_path)["steps"]["clean"].startswith("failed")


def test_no_pull_and_no_upload_flags(sandbox, monkeypatch):
    tmp_path, calls = sandbox
    monkeypatch.setattr(daily, "fetch", lambda step: None)
    monkeypatch.setattr(daily, "clean", lambda: None)
    monkeypatch.setattr(daily.forecast, "main", lambda: None)
    assert daily.main(["--no-pull", "--no-upload"]) == 0
    assert calls == []
    assert status(tmp_path)["ok"] is True


def test_fetch_asks_for_the_last_week(monkeypatch):
    seen = []
    monkeypatch.setattr(daily.ingest, "main", lambda argv: seen.append(argv))
    daily.fetch(["air", "--kind", "days"])
    daily.fetch(["weather", "--recent"])
    daily.fetch(["fires", "--refresh"])
    assert seen[0][:3] == ["air", "--kind", "days"] and seen[0][3] == "--start"
    assert seen[1] == ["weather", "--recent"]  # the forecast call takes no dates
    assert seen[2][:2] == ["fires", "--refresh"] and seen[2][2] == "--start"


def test_hourly_fetch_asks_up_to_the_start_of_the_next_day(monkeypatch, tmp_path):
    """Regression: hourly requests stop before their end time, so asking 'up to today'
    used to drop everything measured today."""
    from datetime import date

    import pandas as pd

    from breathe_check import ingest

    station = ingest.openaq.Station(
        1,
        "S",
        "indore",
        "CPCB",
        "",
        22.7,
        75.8,
        True,
        (10,),
        None,
        pd.Timestamp.now(tz="UTC").isoformat(),
    )
    monkeypatch.setattr(settings, "RAW_DIR", tmp_path)
    monkeypatch.setattr(ingest, "load_stations", lambda: [station])
    monkeypatch.setattr(ingest.openaq, "sensor_date_ranges", lambda *a, **k: {10: (None, None)})
    monkeypatch.setattr(ingest, "openaq_limiter", lambda: None)
    monkeypatch.setattr(ingest.settings, "need", lambda name: "key")
    seen = {}

    def fake_fetch(client, st, kind, start, end, limiter, sensor_ids=None):
        seen["end"] = end
        return pd.DataFrame()

    monkeypatch.setattr(ingest.openaq, "fetch_station", fake_fetch)
    ingest.main(
        [
            "air",
            "--kind",
            "hours",
            "--cities",
            "indore",
            "--start",
            "2026-11-20",
            "--end",
            "2026-11-27",
        ]
    )
    assert seen["end"] == date(2026, 11, 28)
