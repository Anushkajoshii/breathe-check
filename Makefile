.PHONY: setup test lint format clean stations backfill daily daily-local upload clean-data docs-data figures models grap indore forecast run-window site site-serve

setup:        ## install everything and turn on pre-commit
	uv sync
	uv run pre-commit install

test:         ## run the unit tests
	uv run pytest -q

lint:         ## check code style
	uv run ruff check .
	uv run ruff format --check .

format:       ## fix code style
	uv run ruff check --fix .
	uv run ruff format .

clean:        ## remove local caches and data
	rm -rf .pytest_cache .ruff_cache data/clean data/cache

INGEST = uv run python -m breathe_check.ingest

stations:     ## find CPCB PM2.5 stations near each city
	$(INGEST) stations

backfill:     ## download full history (slow: OpenAQ allows ~2000 calls an hour)
	$(INGEST) air --kind days --start 2018-01-01
	$(INGEST) air --kind hours --start 2025-02-01 --per-city 4
	$(INGEST) weather --start 2018-01-01
	$(INGEST) fires --start 2018-01-01

daily:        ## the full daily update: pull, fetch last week, clean, forecast, upload
	uv run python -m breathe_check.daily

daily-local:  ## the daily update using data already on disk, without uploading
	uv run python -m breathe_check.daily --no-pull --no-upload

upload:       ## copy data/raw to the Hugging Face dataset
	$(INGEST) upload

DBT = uv run dbt

clean-data:   ## run the cleaning rules and build the analysis tables (data/clean/*.parquet)
	mkdir -p data/clean
	$(DBT) build --project-dir transform --profiles-dir transform

docs-data:    ## open dbt's browsable docs for the tables
	$(DBT) docs generate --project-dir transform --profiles-dir transform && $(DBT) docs serve --project-dir transform --profiles-dir transform

figures:      ## draw the charts in reports/figures from the clean tables
	uv run python analysis/first_look.py

models:       ## train the weather-only models and save weather-adjusted PM2.5
	uv run python analysis/deweather.py

grap:         ## did GRAP work? event study, comparison cities, placebo, synthetic control
	uv run python analysis/grap_effect.py

indore:       ## Indore vs India's limits, WHO and its neighbours
	uv run python analysis/indore.py

forecast:     ## make tomorrow's run-window forecast for every city (data/public/forecast)
	uv run python -m breathe_check.forecast

run-window:   ## test the run-window forecast on recent months and draw its charts
	uv run python analysis/run_window.py

site:         ## build the report website into site_build/ (fails on broken links)
	uv run --group site python tools/build_site.py

site-serve:   ## preview the report website at http://127.0.0.1:8000
	uv run --group site python tools/build_site.py --serve
