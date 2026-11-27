"""Save data as Parquet files on disk, and copy them to Hugging Face.

Layout (one file per place per year, so daily updates only rewrite one file):

    data/raw/<source>/<place>/<year>.parquet

e.g. data/raw/air_daily/delhi/2021.parquet
"""

from pathlib import Path

import pandas as pd

from breathe_check import settings


def save_by_year(
    frame: pd.DataFrame,
    source: str,
    place_col: str,
    time_col: str,
    keys: list[str],
    root: Path | None = None,
) -> list[Path]:
    """Merge new rows into the yearly files, replacing rows that have the same keys."""
    if frame.empty:
        return []
    root = root or settings.RAW_DIR
    written = []
    years = frame[time_col].dt.year
    for (place, year), part in frame.groupby([frame[place_col], years]):
        path = root / source / str(place) / f"{year}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            part = pd.concat([pd.read_parquet(path), part], ignore_index=True)
        part = part.drop_duplicates(keys, keep="last").sort_values(keys).reset_index(drop=True)
        part.to_parquet(path, index=False)
        written.append(path)
    return written


def read_source(source: str, root: Path | None = None) -> pd.DataFrame:
    root = root or settings.RAW_DIR
    files = sorted((root / source).glob("*/*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def upload_to_hub(folder: Path | None = None, message: str = "Update data") -> str:
    """Copy data/raw, and data/clean and data/public if built, to the Hugging Face dataset."""
    from huggingface_hub import HfApi

    api = HfApi(token=settings.need("HF_TOKEN"))
    repo_id = settings.get("HF_DATASET_REPO", "Anushkajoshii/breathe-check-data")
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=str(folder or settings.RAW_DIR),
        path_in_repo="raw",
        ignore_patterns=["_progress/*"],
        commit_message=message,
    )
    clean = settings.DATA_DIR / "clean"
    if folder is None and any(clean.glob("*.parquet")):
        api.upload_folder(
            repo_id=repo_id,
            repo_type="dataset",
            folder_path=str(clean),
            path_in_repo="clean",
            allow_patterns=["*.parquet"],
            commit_message=message,
        )
    public = settings.DATA_DIR / "public"
    if folder is None and public.exists():
        api.upload_folder(
            repo_id=repo_id,
            repo_type="dataset",
            folder_path=str(public),
            path_in_repo="public",
            allow_patterns=["*.json", "**/*.json", "*.ics", "**/*.ics"],
            commit_message=message,
        )
    card = settings.ROOT / "docs" / "hf-dataset-card.md"
    if card.exists():
        api.upload_file(
            repo_id=repo_id,
            repo_type="dataset",
            path_or_fileobj=str(card),
            path_in_repo="README.md",
            commit_message="Update dataset card",
        )
    return f"https://huggingface.co/datasets/{repo_id}"


def pull_from_hub(patterns: tuple[str, ...] = ("raw/*", "raw/**")) -> Path:
    """Download the raw data from the Hugging Face dataset into data/, so a fresh
    machine (like the daily GitHub Actions job) can carry on from where we left off."""
    from huggingface_hub import snapshot_download

    repo_id = settings.get("HF_DATASET_REPO", "Anushkajoshii/breathe-check-data")
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=str(settings.DATA_DIR),
        allow_patterns=list(patterns),
        token=settings.get("HF_TOKEN") or None,
    )
    return settings.DATA_DIR
