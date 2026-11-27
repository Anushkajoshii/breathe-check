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

Updated every evening at 7 pm India time by a GitHub Actions job.

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
| `clean/city_day_adjusted.parquet` | Weather-adjusted PM2.5: actual, what the weather predicts, and the ratio | LightGBM weather-only model per city |
| `clean/deweather_scores.parquet` | How well each city's weather model predicts seasons it never saw | Same |
| `clean/city_season_summary.parquet` | Each city and full year (July-June): average PM2.5, days over India's and WHO's limits, cigarette equivalent | Project analysis |
| `clean/weather_fair_ranking.parquet` | Each city vs one shared weather model, 2025-26 | Project analysis |
| `clean/grap_*.parquet` | GRAP event-study, placebo and synthetic-control results | Project analysis |
| `public/forecast/<city>.json` | Tomorrow's hourly PM2.5 forecast (low, middle, high), best 2-hour window, last-24-hours card, smoke check | Made every evening |
| `public/forecast/index.json` | List of cities and their best windows | Made every evening |
| `public/status.json` | When the last daily update ran, what worked, and how fresh each source is | Made every evening |

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
