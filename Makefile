.PHONY: setup test lint format clean stations backfill daily upload

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

daily:        ## fetch the last week of everything plus the weather forecast
	$(INGEST) air --kind days
	$(INGEST) air --kind hours
	$(INGEST) weather
	$(INGEST) weather --recent
	$(INGEST) fires

upload:       ## copy data/raw to the Hugging Face dataset
	$(INGEST) upload
