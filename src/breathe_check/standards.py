"""Air-quality standards and helpers that turn PM2.5 numbers into plain words.

Sources:
- India NAAQS 2009 (CPCB): PM2.5 limit 60 ug/m3 (24-hour) and 40 ug/m3 (annual).
- WHO Global Air Quality Guidelines 2021: 15 ug/m3 (24-hour) and 5 ug/m3 (annual).
- CPCB National AQI (2014) breakpoints for PM2.5 (24-hour average).
- Berkeley Earth rule of thumb: breathing 22 ug/m3 of PM2.5 for a day is roughly
  as harmful as smoking one cigarette. It is a rough comparison, not a medical fact.
"""

from dataclasses import dataclass

INDIA_DAILY_PM25 = 60.0
INDIA_ANNUAL_PM25 = 40.0
WHO_DAILY_PM25 = 15.0
WHO_ANNUAL_PM25 = 5.0

PM25_PER_CIGARETTE = 22.0


@dataclass(frozen=True)
class AqiBand:
    name: str
    pm_low: float
    pm_high: float
    aqi_low: int
    aqi_high: int
    advice: str


# CPCB PM2.5 breakpoints. The top band has no official upper PM2.5 value;
# we use 380 so the line keeps a sensible slope, and cap the AQI at 500.
AQI_BANDS: tuple[AqiBand, ...] = (
    AqiBand("Good", 0, 30, 0, 50, "Great day to be outside."),
    AqiBand(
        "Satisfactory", 30, 60, 51, 100, "Fine for most people. Very sensitive people take it easy."
    ),
    AqiBand(
        "Moderate",
        60,
        90,
        101,
        200,
        "People with asthma, heart issues, kids and elders: keep long runs short.",
    ),
    AqiBand("Poor", 90, 120, 201, 300, "Cut down long or hard exercise outside."),
    AqiBand(
        "Very Poor",
        120,
        250,
        301,
        400,
        "Move your workout indoors. Wear an N95 if you must go out.",
    ),
    AqiBand("Severe", 250, 380, 401, 500, "Stay indoors. Avoid all exercise outside."),
)


def pm25_to_aqi(pm25: float) -> int:
    """Convert a 24-hour PM2.5 average (ug/m3) to India's AQI number (0 to 500)."""
    if pm25 < 0:
        raise ValueError("PM2.5 cannot be negative")
    for band in AQI_BANDS:
        if pm25 <= band.pm_high:
            share = (pm25 - band.pm_low) / (band.pm_high - band.pm_low)
            return round(band.aqi_low + share * (band.aqi_high - band.aqi_low))
    return 500


def aqi_band(pm25: float) -> AqiBand:
    """The CPCB category (Good, Poor, ...) for a PM2.5 value."""
    if pm25 < 0:
        raise ValueError("PM2.5 cannot be negative")
    for band in AQI_BANDS:
        if pm25 <= band.pm_high:
            return band
    return AQI_BANDS[-1]


def cigarettes_per_day(pm25_daily_mean: float) -> float:
    """Roughly how many cigarettes a day of breathing this air is like."""
    if pm25_daily_mean < 0:
        raise ValueError("PM2.5 cannot be negative")
    return round(pm25_daily_mean / PM25_PER_CIGARETTE, 1)


def times_over_limit(pm25: float, limit: float) -> float:
    """How many times over a limit a value is, e.g. 45 vs WHO's 15 -> 3.0."""
    return round(pm25 / limit, 1)
