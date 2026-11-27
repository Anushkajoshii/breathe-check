import pandas as pd

from breathe_check import storage


def frame(values, start="2021-12-30"):
    times = pd.date_range(start, periods=len(values), freq="D", tz="UTC")
    return pd.DataFrame({"city": "delhi", "time_utc": times, "value": values})


def test_rows_are_split_into_yearly_files(tmp_path):
    written = storage.save_by_year(
        frame([1, 2, 3]), "air", "city", "time_utc", ["city", "time_utc"], tmp_path
    )
    assert sorted(p.name for p in written) == ["2021.parquet", "2022.parquet"]


def test_saving_again_replaces_matching_rows(tmp_path):
    keys = ["city", "time_utc"]
    storage.save_by_year(frame([1, 2]), "air", "city", "time_utc", keys, tmp_path)
    storage.save_by_year(frame([9], start="2021-12-31"), "air", "city", "time_utc", keys, tmp_path)
    data = storage.read_source("air", tmp_path)
    assert data["value"].tolist() == [1, 9]


def test_empty_frame_writes_nothing(tmp_path):
    assert storage.save_by_year(pd.DataFrame(), "air", "city", "time_utc", ["city"], tmp_path) == []
