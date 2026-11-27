# Breathe Check

**Honest answers about India's air, from public data.**

Breathe Check answers three questions that matter to people who live in Indian cities:

1. **Did Delhi's GRAP pollution rules actually cut PM2.5, or did the weather do it?**
   Air gets cleaner when the wind picks up or it rains, so a simple before/after hides the truth. We remove the weather effect first, then compare Delhi-NCR with similar cities that have no GRAP.
2. **Indore keeps winning "India's cleanest city". Is its air clean too?**
   Cleanliness rankings measure waste, not air. We compare Indore's PM2.5 with India's limits, the WHO guideline and similar cities, season by season.
3. **When is the safest time to run outside tomorrow?**
   A next-24-hour forecast for your city, with a range showing how sure it is, and the best 2-hour window to go out.

Extras:

- **Cigarette equivalent**: today's air turned into "like smoking N cigarettes", so the numbers mean something.
- **Stubble-smoke check**: NASA fire counts in Punjab and Haryana plus wind direction answer "is crop-fire smoke blowing into Delhi today?"
- **Run-window calendar**: add one link to Google or Apple Calendar, and every evening it puts tomorrow's best 2-hour run window in your calendar, with the AQI. No app, no sign-up, no messages.

> Status: in progress. Live links will appear here as each part ships.

## How it works (short version)

| Step | What happens | Tool |
|---|---|---|
| Collect | Hourly PM2.5 from government (CPCB) stations, hourly weather, crop-fire counts | OpenAQ, Open-Meteo, NASA FIRMS |
| Store | Daily Parquet files in a public dataset | Hugging Face Datasets |
| Clean | Flag stuck sensors, zeros, impossible jumps and gaps; every rule is a tested check ([rules](docs/cleaning-rules.md)) | dbt + DuckDB |
| Analyse | Remove the weather effect, then test whether GRAP worked | LightGBM, statsmodels, synthetic control |
| Share | A full write-up with charts, a run-window web app, a calendar feed | Quarto on GitHub Pages, Vercel, iCalendar |

Everything runs on free tiers. No cloud bill. See [docs/adr](docs/adr) for why each choice was made.

## Results so far

Every number here comes from code in this repo that anyone can re-run. Write-ups so far: [first look at the data](reports/01-first-look.md), [taking the weather out](reports/02-weather-adjusted.md) , [did GRAP work?](reports/03-did-grap-work.md) , [India's cleanest city: is its air clean?](reports/04-indore.md) and [when to run tomorrow](reports/05-run-window.md)

![Tomorrow's run window for Indore](reports/figures/16_indore_tomorrow.png)

- **Delhi in November and December** averages 213 µg/m³ of PM2.5: more than 3.5 times India's daily limit, about 14 times the WHO guideline.
- **Indore**, India's cleanest city by its waste ranking, averaged 41 µg/m³ in July 2025 to June 2026: the cleanest of its neighbours, but right at India's yearly limit (40) and 8 times the WHO guideline. Judged against its weather, it's ordinary.
- **The day after Diwali** is about twice as polluted as the week before, in Delhi and in Indore.
- **Afternoons are cleanest.** In winter, Delhi's air at 5 pm has about 40% less PM2.5 than at midnight.
- **The run-window forecast** misses by about 12 µg/m³ an hour on months it never saw, beats simple rules of thumb, and its low-to-high range holds the real value 80% of the time. Its best window was among the day's cleanest third on 63% of days, against 48% for always running at 2 pm.
- **Weather alone** moves Delhi's winter PM2.5 by about 40%. A weather-only model predicts 80% of Delhi's day-to-day ups and downs on winters it never saw.
- **November 2025 was 48% dirtier than its weather explains.**
- **Did GRAP's strictest stages cut PM2.5 in their first week? We can't find it.** Raw numbers swing +37% after the stages switch on and −31% after they switch off, but that's the bad spells themselves. With weather taken out and Delhi-NCR compared with similar cities that have no GRAP, the change is +8% (90% range −5% to +23%), no different from random dates. Only four events fall in the data, so this is weak evidence, but a large quick cut is hard to believe.

## Run it yourself

You need [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```bash
git clone https://github.com/Anushkajoshii/breathe-check.git
cd breathe-check
make setup
make test
```

Copy `.env.example` to `.env` and add your free API keys (the file says where to get each one). Then collect the data:

```bash
make stations      # find government PM2.5 stations near each city
make backfill      # full history (about an hour, because of API limits)
make daily         # just the last week; this is what the daily job runs
make clean-data    # run the cleaning rules and build the analysis tables
```

You can also skip collecting and read the public dataset on Hugging Face directly.

## The app

A small web page that answers one question for 20 Indian cities: **when is it safest to be outside tomorrow?** It shows the best 2-hour window, an hour-by-hour forecast with a range, the last 24 hours as cigarettes, and, for Delhi-NCR, whether crop-fire smoke is likely. It reads the forecasts the daily job uploads, so it's always fresh.

- Code: [`web/`](web) (React, Vite, TypeScript). Run it locally with `cd web && npm install && npm run dev`.
- Putting it online: [docs/deploy-web.md](docs/deploy-web.md).

## How it stays fresh

Every evening at 7 pm India time, a GitHub Actions job fetches the last week of data, cleans it, makes tomorrow's forecasts and uploads them to Hugging Face. It needs no server and costs nothing. See [the daily update](docs/daily-update.md).

## Known limitations

- Monitoring stations are not spread evenly. Some cities have one or two, so one bad sensor can skew a whole city.
- OpenAQ republishes CPCB data. If CPCB data is late or missing, so is ours.
- The cigarette comparison is a rough rule of thumb from Berkeley Earth, not a medical measure.
- OpenAQ has almost no CPCB data from November 2022 to February 2025, so three winters are missing. See the [data card](docs/data-card.md).
- This is not medical advice. If you have asthma or a heart condition, follow your doctor.

## Licence

MIT. Data comes from its original sources under their own terms, listed in the [data card](docs/data-card.md).
