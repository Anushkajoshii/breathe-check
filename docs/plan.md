# Build plan

Each part is one branch and one pull request.

| Part | What it adds | Status |
|---|---|---|
| 1 | Repo setup, city list, AQI and cigarette helpers, tests, CI, decision records | Done |
| 2 | Data collection: OpenAQ air quality, Open-Meteo weather, NASA crop fires, upload to Hugging Face | Done |
| 3 | GRAP stage dates CSV with sources, Diwali dates | Done |
| 4 | Cleaning with dbt + DuckDB: stuck sensors, spikes, gaps, all as tests | Done |
| 5 | First look at the data: seasons, hours, station coverage | Done |
| 6 | Weather-adjusted PM2.5 ("deweathering") model and checks | Done |
| 7 | Did GRAP work? Event study, difference-in-differences, synthetic control | Done |
| 8 | Indore vs India's limits, WHO and peer cities | To do |
| 9 | Run-window forecast with uncertainty, cigarette equivalent, stubble-smoke check | Done |
| 10 | Daily data workflow on GitHub Actions | Done |
| 11 | Web app on Vercel | Done: https://breathe-check-flax.vercel.app |
| 12 | Calendar feed: tomorrow's best run window added to your calendar every evening | In review |
| 13 | Full report on GitHub Pages, README results, demo GIF, Medium draft | To do |
