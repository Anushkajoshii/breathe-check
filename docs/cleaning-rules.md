# Cleaning rules

Raw readings from pollution monitors are messy. Sensors get stuck, send zeros when they're offline, jump to impossible numbers, or report for only a few hours a day. If we averaged everything, a single broken sensor could move a whole city's number.

**How it works**
- Every reading gets a yes/no flag for each rule below. Nothing is deleted.
- The clean tables leave out flagged readings, and the quality report counts how many each rule caught.
- The rules live in `transform/models/intermediate/` (dbt + DuckDB). `tests/test_cleaning.py` runs them on a small fake dataset with planted problems and checks each rule catches exactly those, and nothing else.

Run it yourself: `make clean-data`.

## Daily readings (one value per station per day)

| Rule | What it catches | Why this line |
|---|---|---|
| Impossible | Below 1 or above 999 µg/m³ | Monitors top out near 1000. A whole day under 1 doesn't happen in an Indian city; it's an offline sensor sending zeros. |
| Incomplete | The station reported less than two-thirds of the day | India's air quality standard needs at least 16 of 24 hours for a valid daily average. |
| Flat | The value didn't change at all for a full day | Real air always moves. A flat line is a stuck sensor. |
| Repeated | Exactly the same daily value three days in a row | Two equal days can happen by chance. Three, to the decimal point, means a stuck feed. All three days are flagged. |
| City outlier | More than 3 times the median of the city's other stations that day, and at least 100 above it | Needs at least 3 other stations to compare with. Catches one station reporting a local fault or a unit mix-up. |

## Hourly readings

| Rule | What it catches | Why this line |
|---|---|---|
| Impossible | Below 0 or above 999 µg/m³ | One clean hour can be close to 0, so the low line is 0 here, not 1. |
| Incomplete | Under half of the hour's 15-minute readings arrived | One reading out of four isn't an hourly average. |
| Stuck | The same value 6 hours in a row | All 6 hours are flagged. |
| Spike | More than 3 times the median of the 3 hours either side, and at least 150 above it | Real pollution builds up and clears over hours. A one-hour jump that vanishes is a sensor glitch. Diwali night still gets through, because the hours around it are high too. |

## What the rules caught (full data, November 2026)

| Level | Readings | Impossible | Incomplete | Flat or stuck | Repeated | Outlier or spike | Removed (any rule) |
|---|---|---|---|---|---|---|---|
| Daily | 219,478 | 1,640 | 43,029 | 1,310 | 2,101 | 1,394 | 45,847 (20.9%) |
| Hourly | 977,989 | 105 | 26,526 | 13,688 | – | 1,057 | 40,935 (4.2%) |

A reading can break more than one rule, so the columns add up to more than the total.

**What stands out**
- **Missing hours are the biggest problem by far.** In 2021, 48% of station-days were incomplete: many stations sent only one or two readings a day through OpenAQ that year. Other years range from 7% to 34%.
- **Zeros:** 1,458 daily readings sat between 0 and 1. These are offline sensors, and they made cities look cleaner than they are. For example, Indore's 2026 average goes from 37 µg/m³ before cleaning to 41 after, which tips it over India's yearly limit of 40.
- **Worst readings:** one Bengaluru station reported 104,000 µg/m³ for several days in late 2025, about a hundred times anything physical. Two rules catch it.
- **Least usable stations:** Vijay Nagar in Indore is usable on only 36% of the days it reported. See `station_quality` for every station.

## The tables this produces

Written to `data/clean/` and uploaded to the `clean/` folder of the Hugging Face dataset:

| Table | One row per | Used for |
|---|---|---|
| `city_day` | City and day | Everything: GRAP, Indore, trends. Has PM2.5, the number of stations behind it, daily weather, GRAP stage, original GRAP season, days from Diwali, and crop fires today and yesterday. |
| `city_hour` | City and hour (Feb 2025 onwards) | The run-window forecast |
| `station_quality` | Station | Spotting broken stations |
| `quality_report` | Level (daily or hourly) | The table above |

## Things to keep in mind

- **The station mix changes.** The 2018–2022 network and the 2025-onwards network aren't the same set of stations. City averages before and after aren't perfectly comparable, so the analysis compares cities within the same period wherever it can.
- **Delhi-NCR overlap:** the NCR cities are close together, but each station counts for one city only (the one it's closest to).
- **Order dates:** GRAP stages count from the day the order was issued. The analysis also tries starting from the next day, because orders often come out in the afternoon.
