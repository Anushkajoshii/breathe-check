import pandas as pd

from breathe_check import grap


def orders(rows):
    frame = pd.DataFrame(rows, columns=["order_date", "action", "stage"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    frame["source_url"] = "https://example.test"
    return frame


def test_real_orders_file_has_no_problems():
    assert grap.check_orders(grap.load_orders()) == []


def test_every_order_has_a_review_flag():
    assert set(grap.load_orders()["needs_review"]) <= {"yes", "no"}


def test_stages_stack_and_revoke_drops_to_the_stage_below():
    assert grap.apply(0, "invoke", 3) == 3
    assert grap.apply(3, "invoke", 1) == 3  # invoking a lower stage changes nothing
    assert grap.apply(4, "revoke", 3) == 2  # revoking III also ends IV
    assert grap.apply(2, "revoke", 1) == 0


def test_daily_stage_follows_orders():
    o = orders(
        [
            ("2025-10-14", "invoke", 1),
            ("2025-10-16", "invoke", 3),
            ("2025-10-18", "revoke", 3),
        ]
    )
    daily = grap.daily_stage(o, end="2025-10-19")
    assert daily["grap_stage"].tolist() == [1, 1, 3, 3, 2, 2]


def test_check_catches_a_revoke_of_a_stage_that_was_off():
    o = orders([("2025-10-14", "invoke", 1), ("2025-10-15", "revoke", 3)])
    assert "revokes stage 3 but only stage 1 was on" in grap.check_orders(o)[0]


def test_check_catches_dates_out_of_order():
    o = orders([("2025-10-15", "invoke", 1), ("2025-10-14", "invoke", 2)])
    assert "orders are not in date order" in grap.check_orders(o)


def test_diwali_is_in_october_or_november_every_year():
    diwali = grap.load_diwali()
    assert diwali["year"].tolist() == list(range(2018, 2027))
    assert diwali["date"].dt.month.isin([10, 11]).all()
    assert (diwali["date"].dt.year == diwali["year"]).all()


def test_original_seasons_run_october_to_march():
    seasons = grap.load_original_seasons()
    assert (seasons["start"].dt.strftime("%m-%d") == "10-15").all()
    assert (seasons["end"].dt.strftime("%m-%d") == "03-15").all()
