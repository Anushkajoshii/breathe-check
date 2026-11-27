# The daily update

Every evening at **7 pm India time**, a GitHub Actions job:
1. downloads the latest data
2. cleans it
3. makes tomorrow's forecasts
4. uploads everything to the [Hugging Face dataset](https://huggingface.co/datasets/Anushkajoshii/breathe-check-data)

Why it's built this way: [ADR-004](adr/004-daily-update-on-github-actions.md).

## One-time setup: add the keys

The job needs three keys, stored as encrypted GitHub secrets. Run this from the project folder. It reads them straight from your `.env` file:

```bash
gh secret set -f .env -R Anushkajoshii/breathe-check
```

To check they're there (this shows only the names, never the values):

```bash
gh secret list -R Anushkajoshii/breathe-check
```

You should see `OPENAQ_API_KEY`, `FIRMS_MAP_KEY` and `HF_TOKEN`.

## Run it now

- **Website:** the repo's **Actions** tab → **Daily update** → **Run workflow**.
- **Terminal:**

```bash
gh workflow run daily.yml -R Anushkajoshii/breathe-check
```

- **On your own machine,** the same steps without uploading:

```bash
make daily-local
```

## Is it working?

- **Actions tab:** a green tick means the forecast was made and uploaded. Red means cleaning or the forecast failed, and yesterday's files are still up.
- **`public/status.json` on Hugging Face** says, for the latest run:
  - when it ran
  - which steps worked (`"ok"`) and which failed, with the error
  - how fresh each source is (`data_up_to`)

A failed data source, for example `"fetch_fires": "failed: ..."`, doesn't stop the forecast. It just means that source is a day older than usual. If the same source fails several days in a row, check whether the API key has expired or the API has changed.

## Things to know

- **The 60-day pause:** GitHub pauses scheduled jobs in a repo with no new commits for 60 days. If that happens, the Actions tab shows a banner with an **Enable workflow** button. Pushing any change also wakes it up.
- **Run time:** about 15 minutes (a full test run from an empty machine took 13.5), mostly waiting on OpenAQ's limit of 60 calls a minute.
- **Cost:** nothing. GitHub Actions is free for public repos, and Hugging Face datasets are free.
- **New stations:** the job uses the station list already saved. To pick up new CPCB stations, run `make stations` and then `make upload` from time to time.
