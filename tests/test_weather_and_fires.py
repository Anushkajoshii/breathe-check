from datetime import date

import httpx

from breathe_check.cities import get_city
from breathe_check.sources import firms, weather

FIRE_HEADER = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,"
    "instrument,confidence,version,bright_ti5,frp,daynight,type\n"
)
FIRE_CSV = (
    FIRE_HEADER
    + """30.1,75.2,340.1,0.5,0.4,2024-11-01,826,N,VIIRS,n,2,305.3,3.2,D,0
30.1,75.2,340.1,0.5,0.4,2024-11-01,826,N,VIIRS,n,2,305.3,3.2,D,0
29.9,76.0,330.0,0.5,0.4,2024-11-02,2015,N,VIIRS,l,2,300.1,1.1,N,0
"""
)


def test_weather_is_parsed_into_utc_rows():
    payload = {
        "hourly": {"time": ["2024-11-01T00:00", "2024-11-01T01:00"], "wind_speed_10m": [3.1, 2.0]}
    }
    frame = weather.parse_hourly(payload, get_city("delhi"))
    assert list(frame.columns) == ["city", "wind_speed_10m", "time_utc"]
    assert str(frame["time_utc"].dt.tz) == "UTC"


def test_weather_history_asks_one_year_at_a_time():
    asked = []

    def handler(request):
        asked.append((request.url.params["start_date"], request.url.params["end_date"]))
        return httpx.Response(
            200, json={"hourly": {"time": ["2020-01-01T00:00"], "precipitation": [0]}}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    weather.fetch_history(client, get_city("indore"), date(2020, 6, 1), date(2021, 2, 1))
    assert asked == [("2020-06-01", "2020-12-31"), ("2021-01-01", "2021-02-01")]


def test_fire_csv_parsing_builds_utc_time():
    frame = firms.parse_csv(FIRE_CSV)
    assert len(frame) == 3
    assert str(frame.loc[0, "time_utc"]) == "2024-11-01 08:26:00+00:00"
    assert str(frame.loc[2, "time_utc"]) == "2024-11-02 20:15:00+00:00"


def test_fire_api_message_is_not_mistaken_for_data():
    assert firms.parse_csv("").empty


def test_date_chunks_cover_range_in_5_day_steps():
    chunks = list(firms.date_chunks(date(2024, 10, 1), date(2024, 10, 12)))
    assert chunks == [(date(2024, 10, 1), 5), (date(2024, 10, 6), 5), (date(2024, 10, 11), 2)]


def test_fetch_fires_uses_final_data_when_available_and_dedupes():
    asked = []

    def handler(request):
        path = request.url.path
        if "data_availability" in path:
            return httpx.Response(
                200,
                text="data_id,min_date,max_date\nVIIRS_SNPP_SP,2012-01-20,2024-10-31\n"
                "VIIRS_SNPP_NRT,2024-09-01,2024-12-31\n",
            )
        asked.append(path.split("/")[5])
        return httpx.Response(200, text=FIRE_CSV)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    frame = firms.fetch_fires(client, "KEY", date(2024, 10, 27), date(2024, 11, 5))
    assert asked == ["VIIRS_SNPP_SP", "VIIRS_SNPP_NRT"]
    assert len(frame) == 2  # the duplicate row is removed


def test_fire_limit_message_makes_us_wait_and_retry():
    replies = iter(
        [
            httpx.Response(400, text="Exceeding allowed transaction limit."),
            httpx.Response(200, text=FIRE_CSV),
        ]
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda request: next(replies)))
    waits = []
    text = firms.get_csv(client, "https://x.test/a", sleep=waits.append)
    assert waits == [60]
    assert text.startswith("latitude")


def test_fire_version_is_always_text():
    nrt = FIRE_CSV.replace(",2,305.3,3.2,D,0", ",2.0NRT,305.3,3.2,D,0")
    assert firms.parse_csv(nrt)["version"].map(type).eq(str).all()


def test_after_suomi_npp_stops_we_switch_to_noaa20():
    last = {
        "VIIRS_SNPP_SP": date(2026, 8, 31),
        "VIIRS_SNPP_NRT": date(2026, 11, 2),
        "VIIRS_NOAA20_NRT": date(2026, 11, 27),
    }
    assert firms.pick_source(date(2026, 8, 30), last) == "VIIRS_SNPP_SP"
    assert firms.pick_source(date(2026, 10, 1), last) == "VIIRS_SNPP_NRT"
    assert firms.pick_source(date(2026, 11, 20), last) == "VIIRS_NOAA20_NRT"
