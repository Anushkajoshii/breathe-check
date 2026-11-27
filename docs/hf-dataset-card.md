---
license: cc-by-4.0
pretty_name: Breathe Check - India air quality, weather and crop fires
language:
  - en
tags:
  - air-quality
  - pm2.5
  - india
  - weather
  - time-series
size_categories:
  - 1M<n<10M
---

# Breathe Check data

Public data behind [Breathe Check](https://github.com/Anushkajoshii/breathe-check), a project that asks:
did Delhi's GRAP pollution rules actually work, is Indore's air as clean as its streets, and when is it safest to run outside?

Updated daily by a GitHub Actions job.

## Files

| Folder | What | From |
|---|---|---|
| `raw/stations.csv` | Government PM2.5 stations near 20 Indian cities | OpenAQ (CPCB) |
| `raw/air_daily/<city>/<year>.parquet` | Daily PM2.5 per station, 2018 onwards | OpenAQ (CPCB) |
| `raw/air_hourly/<city>/<year>.parquet` | Hourly PM2.5, up to 4 stations per city, Feb 2025 onwards | OpenAQ (CPCB) |
| `raw/weather/<city>/<year>.parquet` | Hourly weather at each city centre, 2018 onwards | Open-Meteo (ERA5) |
| `raw/weather_forecast/<city>/<year>.parquet` | Last 7 days plus the next 2 days | Open-Meteo |
| `raw/fires/punjab_haryana/<year>.parquet` | Satellite fire detections in Punjab and Haryana | NASA FIRMS (VIIRS) |
| `clean/city_day.parquet` | One row per city per day: cleaned PM2.5, weather, GRAP stage, Diwali, crop fires | Built by the project's dbt rules |
| `clean/city_hour.parquet` | One row per city per hour (Feb 2025 onwards): cleaned PM2.5 and weather | Built by the project's dbt rules |
| `clean/station_quality.parquet` | Share of usable days per station | Built by the project's dbt rules |

## Read it with DuckDB

```sql
SELECT city, date_trunc('month', start_utc) AS month, avg(value) AS pm25
FROM 'hf://datasets/Anushkajoshii/breathe-check-data/raw/air_daily/delhi/*.parquet'
GROUP BY ALL ORDER BY month;
```

## Important limits

- OpenAQ has almost no CPCB data from November 2022 to February 2025.
- Files in `raw/` are untouched readings. Files in `clean/` leave out readings that break the [cleaning rules](https://github.com/Anushkajoshii/breathe-check/blob/main/docs/cleaning-rules.md).
- Each source keeps its own licence: CPCB (Government of India) via OpenAQ, Open-Meteo (CC BY 4.0), NASA FIRMS. Please credit them.

Full details: [data card](https://github.com/Anushkajoshii/breathe-check/blob/main/docs/data-card.md).
