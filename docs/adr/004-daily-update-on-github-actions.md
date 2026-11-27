# ADR-004: Run the daily update on GitHub Actions, with Hugging Face as the store

**Status:** Accepted, November 2026

## Context

The forecast is only useful if it's made fresh every evening. That needs a machine that:
- wakes up once a day
- downloads the last week of data
- runs the cleaning rules and the forecast
- puts the results somewhere the app can read

ADR-001 rules out AWS for this project.

## Decision

- **A scheduled GitHub Actions workflow** (`.github/workflows/daily.yml`) runs at 13:30 UTC (7 pm India time) every day, and can also be started by hand. It's free for public repositories.
- **The runner starts empty every time.** It first pulls the raw data from the Hugging Face dataset, then fetches the last 7 days on top. Re-fetching a week, not just a day, fills in late readings and the weather archive's few-day delay.
- **Everything goes back to Hugging Face:** raw data, clean tables, forecast JSON files and a `status.json`. The web app reads the forecasts from there directly (Hugging Face allows this from browsers).
- **Secrets** (OpenAQ, NASA FIRMS and Hugging Face keys) live in GitHub's encrypted secrets. They never appear in code or logs.
- **No commits.** The job never commits to the repo, so the history stays the author's own work.

## Failure handling

- **A data source being down doesn't stop the update.** The other sources still run, the forecast is made from the newest data available, and `status.json` records what failed and how fresh each source is.
- **The job fails (red in the Actions tab) only if cleaning or the forecast fails.** In that case nothing is uploaded, and yesterday's files stay up.

## Consequences

- Each run takes about 15 minutes (a full test from an empty machine took 13.5), mostly waiting on OpenAQ's rate limit. The daily run uses 50 calls a minute, which stays under OpenAQ's hourly cap for a one-week fetch.
- **GitHub pauses scheduled workflows** in a repository with no commits for 60 days. Since the job doesn't commit, someone needs to push something (or press "Enable workflow") at least every two months. This is written in `docs/daily-update.md`.
- Hugging Face keeps every daily upload as a version, so any past day's forecast can be looked up.
