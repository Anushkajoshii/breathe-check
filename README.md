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
- **Daily Telegram alert**: tomorrow's best run window for your city, every evening.

> Status: in progress. Live links will appear here as each part ships.

## How it works (short version)

| Step | What happens | Tool |
|---|---|---|
| Collect | Hourly PM2.5 from government (CPCB) stations, hourly weather, crop-fire counts | OpenAQ, Open-Meteo, NASA FIRMS |
| Store | Daily Parquet files in a public dataset | Hugging Face Datasets |
| Clean | Flag stuck sensors, impossible jumps and gaps; every rule is a tested check | dbt + DuckDB |
| Analyse | Remove the weather effect, then test whether GRAP worked | LightGBM, statsmodels, synthetic control |
| Share | A full write-up with charts, a run-window web app, a Telegram bot | Quarto on GitHub Pages, Vercel, Telegram |

Everything runs on free tiers. No cloud bill. See [docs/adr](docs/adr) for why each choice was made.

## Results

Coming soon. Every number here will come from code in this repo that anyone can re-run.

## Run it yourself

You need [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```bash
git clone https://github.com/Anushkajoshii/breathe-check.git
cd breathe-check
make setup
make test
```

Copy `.env.example` to `.env` and add your free API keys (the file says where to get each one).

## Known limitations

- Monitoring stations are not spread evenly. Some cities have one or two, so one bad sensor can skew a whole city.
- OpenAQ republishes CPCB data. If CPCB data is late or missing, so is ours.
- The cigarette comparison is a rough rule of thumb from Berkeley Earth, not a medical measure.
- This is not medical advice. If you have asthma or a heart condition, follow your doctor.

## Licence

MIT. Data comes from its original sources under their own terms (listed in the data card, coming in Part 2).
