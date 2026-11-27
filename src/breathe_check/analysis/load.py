"""Load the clean tables, from disk if built locally, otherwise from Hugging Face."""

from pathlib import Path

import duckdb
import pandas as pd

from breathe_check import settings

HF_CLEAN = "hf://datasets/{repo}/clean/{name}.parquet"


def table_path(name: str) -> str:
    local = settings.DATA_DIR / "clean" / f"{name}.parquet"
    if local.exists():
        return str(local)
    repo = settings.get("HF_DATASET_REPO", "Anushkajoshii/breathe-check-data")
    return HF_CLEAN.format(repo=repo, name=name)


def load(name: str, where: str | None = None, path: str | Path | None = None) -> pd.DataFrame:
    """Read one clean table, e.g. load("city_day", "city = 'delhi'")."""
    source = str(path) if path else table_path(name)
    query = f"select * from read_parquet('{source}')"
    if where:
        query += f" where {where}"
    return duckdb.sql(query).df()
