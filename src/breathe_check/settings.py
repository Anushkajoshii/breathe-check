"""Settings read from the environment (.env locally, GitHub secrets in CI)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("BREATHE_DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"

load_dotenv(ROOT / ".env")


def need(name: str) -> str:
    """Return a required setting, or stop with a clear message if it is missing."""
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("PASTE_"):
        raise SystemExit(f"{name} is not set. Add it to your .env file (see .env.example).")
    return value


def get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()
