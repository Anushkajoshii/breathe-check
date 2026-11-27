.PHONY: setup dev test lint format ingest clean

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
	rm -rf .pytest_cache .ruff_cache data/raw data/clean data/cache
