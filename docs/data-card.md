# Data card

What data Breathe Check uses, where it comes from, what's wrong with it, and how it's stored.

The data lives on Hugging Face: [Anushkajoshii/breathe-check-data](https://huggingface.co/datasets/Anushkajoshii/breathe-check-data). The code that fetches it is in `src/breathe_check/sources/`.

## 1. Air quality: PM2.5 from government stations

| | |
|---|---|
| What | PM2.5 (fine dust smaller than 2.5 micrometres), in µg/m³ |
| Who measures it | CPCB and state pollution control boards (Continuous Ambient Air Quality Monitoring Stations) |
| How we get it | [OpenAQ API v3](https://docs.openaq.org/), which copies CPCB data |
| Which stations | Fixed government stations (provider "CPCB") within 25 km of each of our 20 cities. A station near two cities goes to the closer one. |
| Daily data | Every station, January 2018 onwards (`raw/air_daily/<city>/<year>.parquet`) |
| Hourly data | Up to 4 live stations per city (closest to the centre), February 2025 onwards (`raw/air_hourly/...`) |
| Licence | Published by Government of India bodies. OpenAQ lists the licence for each station. Cite CPCB and OpenAQ when you use it. |

Columns: `city, location_id, sensor_id, period, start_utc, start_local, value, min, max, sd, observed_count, percent_complete, has_flags`.

`value` is the average for the hour or day. `percent_complete` says how much of that hour or day the station actually reported. `sd` is how much readings moved within the period. An `sd` of 0 over a full day usually means a stuck sensor.

### Known problems

- **The big gap.** OpenAQ has almost no CPCB data from **November 2022 to February 2025**. CPCB stations were given new sensor IDs in February 2025, and the months in between are missing. That gap covers three winters (2022-23, 2023-24 and 2024-25). We still have four winters under the original GRAP (2018-19 to 2021-22) and the winters from 2025-26 on under the revised GRAP. The analysis says clearly which winters it uses.
- **Uneven coverage.** Delhi has 42 stations. Indore has 6, and only one of them (Pithampur industrial area, about 25 km out) has history before 2025.
- **Typical sensor faults.** Stuck values, sudden spikes, long gaps, zeros and negative numbers. Each is flagged by a tested rule, never silently deleted. See [cleaning rules](cleaning-rules.md) for what each rule caught.

## 2. Weather

| | |
|---|---|
| What | Hourly temperature, humidity, dew point, rain, pressure, cloud, wind speed, direction and gusts, boundary-layer (mixing) height, sunlight |
| Source | [Open-Meteo](https://open-meteo.com/): the historical archive (ERA5 reanalysis) and the forecast API |
| Where | One point per city (the city centre) |
| Files | `raw/weather/<city>/<year>.parquet` (history), `raw/weather_forecast/...` (last 7 days and the next 2) |
| Licence | Open-Meteo data is CC BY 4.0. ERA5 is from the Copernicus Climate Change Service. |

Why it matters: when the wind is calm and the mixing height is low, pollution has nowhere to go. Weather explains most day-to-day changes in PM2.5, so we have to take it out before judging any rule.

## 3. Crop fires

| | |
|---|---|
| What | Every fire the VIIRS satellite (Suomi NPP) detected |
| Source | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) area API |
| Where | A box around Punjab and Haryana: longitude 73.8 to 77.6, latitude 27.6 to 32.6 |
| Versions | Standard data (final) where available, near-real-time data for the last 2 to 3 months |
| Files | `raw/fires/punjab_haryana/<year>.parquet` |
| Licence | NASA data is free to use. Please credit NASA FIRMS. |

## 4. Small reference files (kept in this repo)

In [`reference/`](../reference/README.md):
- `grap_orders.csv`: 85 revised-GRAP stage orders (October 2022 to November 2026), each with a source link and a note on how well it's backed up.
- `grap_original_seasons.csv`: the original GRAP season window (15 October to 15 March), 2017-18 to 2021-22.
- `diwali.csv`: Diwali date for each year, 2018 to 2026.

Four rows are marked `needs_review`, where the sources disagree. The analysis is run with and without them.

## Privacy

No personal data. All readings are about places, not people.
