# ADR-002: Keep the data on Hugging Face, not in git

**Status:** Accepted, November 2026

## Context

Hourly readings for about 20 cities, several stations each, over several years, come to hundreds of MB. Git is bad at large files that change every day: the repo grows forever and cloning gets slow.

## Decision

Raw and clean data go to a public Hugging Face dataset (`Anushkajoshii/breathe-check-data`) as Parquet files, split by source, city and month. The repo keeps only code, small reference files (like the GRAP dates CSV), and tests.

## Why Parquet

- Small: compressed by column.
- Fast: DuckDB reads only the columns and months a query needs, even over the internet.
- Typed: timestamps stay timestamps.

## Consequences

- Anyone can reproduce the analysis without our keys, just by reading the public dataset.
- Writing needs a Hugging Face token, kept as a GitHub secret.
- The dataset gets its own data card that lists every source and its licence.
