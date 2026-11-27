import httpx
import pandas as pd

from breathe_check.cities import get_city
from breathe_check.sources import openaq


def location(id_, lat, lon, provider="CPCB", sensors=((101, 2),), mobile=False):
    return {
        "id": id_,
        "name": f"Station {id_}",
        "provider": {"name": provider},
        "owner": {"name": "CPCB"},
        "isMobile": mobile,
        "isMonitor": True,
        "coordinates": {"latitude": lat, "longitude": lon},
        "sensors": [{"id": s, "parameter": {"id": p}} for s, p in sensors],
        "datetimeFirst": {"utc": "2018-03-01T00:00:00Z"},
        "datetimeLast": {"utc": "2026-11-27T00:00:00Z"},
    }


def reading(start_utc, value):
    return {
        "value": value,
        "flagInfo": {"hasFlags": False},
        "period": {
            "label": "1day",
            "datetimeFrom": {"utc": start_utc, "local": start_utc},
        },
        "summary": {"min": value - 5, "max": value + 5, "sd": 2.0},
        "coverage": {"observedCount": 24, "percentComplete": 100.0},
    }


def test_only_fixed_cpcb_pm25_stations_are_kept():
    payload = {
        "results": [
            location(1, 28.6, 77.2),
            location(2, 28.6, 77.2, provider="AirGradient"),
            location(3, 28.6, 77.2, mobile=True),
            location(4, 28.6, 77.2, sensors=((401, 5),)),  # NO2 only
        ]
    }
    stations = openaq.parse_locations(payload, get_city("delhi"))
    assert [s.location_id for s in stations] == [1]
    assert stations[0].pm25_sensor_ids == (101,)


def test_station_goes_to_its_nearest_city():
    # A point in Noida should belong to Noida even when found in Delhi's search
    assert openaq.nearest_city(28.57, 77.36).slug == "noida"


def test_distance_delhi_to_indore_is_about_660_km():
    d = get_city("delhi")
    i = get_city("indore")
    assert 640 < openaq.distance_km(d.lat, d.lon, i.lat, i.lon) < 680


def test_fetch_station_pages_and_removes_duplicates():
    page1 = {"results": [reading("2021-11-01T00:00:00Z", 100)] * 2}

    def handler(request):
        assert request.url.params["date_from"] == "2021-11-01"
        return httpx.Response(200, json=page1)

    client = httpx.Client(base_url="https://x.test", transport=httpx.MockTransport(handler))
    station = openaq.parse_locations({"results": [location(1, 28.6, 77.2)]}, get_city("delhi"))[0]
    frame = openaq.fetch_station(client, station, "days", "2021-11-01", "2021-11-30")
    assert len(frame) == 1
    assert frame.loc[0, "value"] == 100
    assert frame.loc[0, "city"] == "delhi"
    assert isinstance(frame.loc[0, "start_utc"], pd.Timestamp)


def test_fetch_keeps_asking_while_pages_are_full(monkeypatch):
    monkeypatch.setattr(openaq, "PAGE_SIZE", 2)
    pages = {
        "1": [reading("2021-11-01T00:00:00Z", 1), reading("2021-11-02T00:00:00Z", 2)],
        "2": [reading("2021-11-03T00:00:00Z", 3)],
    }

    def handler(request):
        return httpx.Response(200, json={"results": pages[request.url.params["page"]]})

    client = httpx.Client(base_url="https://x.test", transport=httpx.MockTransport(handler))
    rows = [
        r
        for page in openaq.iter_sensor_pages(client, 1, "days", "2021-11-01", "2021-11-30")
        for r in page
    ]
    assert [r["value"] for r in rows] == [1, 2, 3]


def test_month_windows_split_on_month_edges():
    windows = openaq.month_windows("2025-02-15", "2025-04-10")
    assert [(str(a.date()), str(b.date())) for a, b in windows] == [
        ("2025-02-15", "2025-03-01"),
        ("2025-03-01", "2025-04-01"),
        ("2025-04-01", "2025-04-10"),
    ]


def test_overlaps_skips_sensors_retired_before_the_range():
    old = (pd.Timestamp("2018-03-01", tz="UTC"), pd.Timestamp("2022-10-31", tz="UTC"))
    new = (pd.Timestamp("2025-02-18", tz="UTC"), pd.Timestamp("2026-11-27", tz="UTC"))
    assert not openaq.overlaps(old, "2025-02-01", "2026-11-27")
    assert openaq.overlaps(new, "2025-02-01", "2026-11-27")
    assert openaq.overlaps((None, None), "2025-02-01", "2026-11-27")
