import json
from datetime import UTC, datetime

import icalendar
import pytest

from breathe_check import calendar_feed as cf


def forecast(day="2026-11-29", start=12, end=14, smoke=None):
    hours = [
        {"hour": h, "low": 20, "mid": 50.0, "high": 80, "category": "Satisfactory"}
        for h in range(24)
    ]
    return {
        "city": "indore",
        "name": "Indore",
        "for_date": day,
        "hours": hours,
        "worst_hour": 23,
        "best_window": {
            "start": start,
            "end": end,
            "pm25": 28.1,
            "category": "Good",
            "advice": "Great day to be outside.",
        },
        "smoke": smoke,
    }


NOW = datetime(2026, 11, 28, 14, 0, tzinfo=UTC)


def test_india_time_is_written_as_utc():
    e = cf.event_for(forecast())
    assert e["start_utc"] == "20261129T063000Z"  # noon in India = 06:30 UTC
    assert e["end_utc"] == "20261129T083000Z"
    assert e["title"].startswith("Best time to be outside: noon to 2 pm (Good")


def test_no_best_window_means_no_event():
    f = forecast()
    f["best_window"] = None
    assert cf.event_for(f) is None


def test_text_is_escaped_and_long_lines_folded():
    assert cf.escape("a;b,c\\d\nnext") == "a\;b\\,c\\\\d\\nnext"
    folded = cf.fold("DESCRIPTION:" + "µ" * 100)
    assert all(len(part.encode()) <= 75 for part in folded.split("\r\n"))
    assert folded.replace("\r\n ", "") == "DESCRIPTION:" + "µ" * 100


def test_feed_is_readable_by_calendar_software(tmp_path):
    path = cf.update_city(forecast(smoke={"level": "Likely", "why": "2,100 fires."}), NOW, tmp_path)
    cal = icalendar.Calendar.from_ical(path.read_bytes())
    events = list(cal.walk("VEVENT"))
    assert len(events) == 1
    ev = events[0]
    assert ev.decoded("dtstart") == datetime(2026, 11, 29, 6, 30, tzinfo=UTC)
    assert "Crop-fire smoke likely" in str(ev.get("description"))
    assert str(ev.get("uid")) == "indore-2026-11-29@breathe-check"
    assert path.read_bytes().count(b"\r\n") > 10  # calendar files use CRLF line endings


def test_history_keeps_14_days_and_replaces_same_day(tmp_path):
    old = [
        {
            "uid": "x",
            "date": "2026-11-01",
            "start_utc": "",
            "end_utc": "",
            "title": "",
            "description": "",
            "url": "",
        }
    ]
    (tmp_path / "indore.json").write_text(json.dumps(old))
    cf.update_city(forecast("2026-11-28", 14, 16), NOW, tmp_path)
    cf.update_city(forecast("2026-11-29", 12, 14), NOW, tmp_path)
    cf.update_city(
        forecast("2026-11-29", 15, 17), NOW, tmp_path
    )  # a newer forecast for the same day
    history = json.loads((tmp_path / "indore.json").read_text())
    assert [e["date"] for e in history] == ["2026-11-28", "2026-11-29"]  # 1 Nov is too old
    assert "3 pm to 5 pm" in history[-1]["title"]


@pytest.mark.parametrize(("h", "label"), [(0, "midnight"), (12, "noon"), (7, "7 am"), (16, "4 pm")])
def test_hour_labels(h, label):
    assert cf.hour_label(h) == label
