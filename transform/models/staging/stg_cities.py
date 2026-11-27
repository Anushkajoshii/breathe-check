"""The city list and roles, straight from the Python package (one source of truth)."""

import pandas as pd

from breathe_check.cities import CITIES


def model(dbt, session):
    dbt.config(materialized="table")
    return pd.DataFrame([c.__dict__ for c in CITIES])
