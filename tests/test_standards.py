import pytest

from breathe_check.standards import (
    WHO_DAILY_PM25,
    aqi_band,
    cigarettes_per_day,
    pm25_to_aqi,
    times_over_limit,
)


@pytest.mark.parametrize(
    ("pm25", "aqi"),
    [(0, 0), (30, 50), (60, 100), (90, 200), (120, 300), (250, 400), (380, 500), (900, 500)],
)
def test_aqi_matches_cpcb_breakpoints(pm25, aqi):
    assert pm25_to_aqi(pm25) == aqi


def test_aqi_is_linear_inside_a_band():
    # Halfway through "Poor" (90-120 -> 201-300)
    assert pm25_to_aqi(105) == 250


@pytest.mark.parametrize(
    ("pm25", "name"),
    [
        (10, "Good"),
        (45, "Satisfactory"),
        (75, "Moderate"),
        (100, "Poor"),
        (200, "Very Poor"),
        (400, "Severe"),
    ],
)
def test_band_names(pm25, name):
    assert aqi_band(pm25).name == name


def test_cigarettes():
    assert cigarettes_per_day(22) == 1.0
    assert cigarettes_per_day(110) == 5.0
    assert cigarettes_per_day(0) == 0.0


def test_times_over_limit():
    assert times_over_limit(45, WHO_DAILY_PM25) == 3.0


def test_negative_values_are_rejected():
    with pytest.raises(ValueError):
        pm25_to_aqi(-1)
    with pytest.raises(ValueError):
        cigarettes_per_day(-1)
