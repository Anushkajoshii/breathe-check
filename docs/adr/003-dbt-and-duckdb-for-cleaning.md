# ADR-003: Clean the data with dbt and DuckDB

**Status:** Accepted, November 2026

## Context

About a million hourly readings and 220,000 daily readings need the same cleaning rules every day, and every rule needs to be visible and tested. A notebook full of pandas steps would work once, but it's hard to review and easy to break without noticing.

## Decision

- **DuckDB** runs SQL straight over the Parquet files, on a laptop or in GitHub Actions. No database server. A full rebuild takes about 4 seconds.
- **dbt** organises the SQL into layers:
  - `staging`: tidy column names and India-time dates
  - `intermediate`: one flag per cleaning rule
  - `marts`: the tables the analysis reads
- **Tests in two places:**
  - dbt data tests on the real data: unique rows, GRAP only in NCR, no impossible values after cleaning, a full day of weather behind every reading.
  - A pytest suite that runs the whole dbt project on a small fake dataset with planted problems, so every rule is proven to catch exactly what it should.
- The GRAP stage per day is a dbt Python model that reuses `breathe_check.grap`, so the stage logic exists in only one place.

## Why not pandera

The plan first named pandera for data checks. dbt tests cover the same ground (ranges, uniqueness, links between tables), and they run where the data is built. Adding pandera would mean two places to define the same rules.

## Consequences

- Each rule is a few lines of SQL with a comment explaining the threshold. The numbers are in `docs/cleaning-rules.md`.
- `make clean-data` rebuilds everything, and the daily job will run the same command.
- Anyone can browse the tables and how they connect with `make docs-data`.
