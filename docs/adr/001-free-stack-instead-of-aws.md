# ADR-001: Use free hosted tools instead of AWS

**Status:** Accepted, November 2026

## Context

The original plan put the data on S3 and ran jobs on AWS. My AWS free tier is already used by another project (PaperTrail), and a second project there would either cost money or fight for the same limits.

This project does not need a server running all day. It needs:

- a job that runs once a day to fetch new data,
- somewhere to keep a few hundred MB of Parquet files,
- a static report site,
- a small web page and a bot.

## Decision

| Need | AWS version | What we use | Why |
|---|---|---|---|
| Daily job | EventBridge + Lambda | GitHub Actions scheduled workflow | Free for public repos, and the logs sit next to the code |
| Data storage | S3 | Hugging Face Datasets | Free, public, and DuckDB can read the Parquet files straight from a URL |
| Report | S3 + CloudFront | Quarto on GitHub Pages | Free, built from the repo on every merge |
| Web app | Amplify | Vercel | Free hobby plan, deploys from GitHub |
| Alerts | SNS | Telegram bot, sent from GitHub Actions | Free, and people already use Telegram |
| Secrets | SSM Parameter Store | GitHub Actions secrets, `.env` locally | Built in, never stored in the code |

## Consequences

- Nothing to tear down and no bill to watch.
- The dataset is public, which is a plus: anyone can check the numbers.
- GitHub can pause scheduled workflows in a repo with no activity for 60 days. The daily job will commit a small status file, which keeps the repo active.
- If the project ever needs a real API with heavy traffic, it can move to a server later. The analysis code does not depend on where it runs.
