"""Check the GRAP analysis on made-up data where the true effect is known."""

import numpy as np
import pandas as pd
import pytest

from breathe_check.analysis import grap_effect as ge

EVENTS = [pd.Timestamp(d) for d in ("2025-11-15", "2025-12-15", "2026-01-15", "2026-02-10")]


def make_panel(effect=0.0, regional_shock=True, seed=0):
    """3 GRAP cities and 3 comparison cities. A regional bad spell peaks just before
    each event and then clears for everyone. GRAP cities get `effect` (log) after."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-10-01", "2026-03-01", freq="D")
    rows = []
    for city, role in [
        ("a", "grap"),
        ("b", "grap"),
        ("c", "grap"),
        ("x", "control"),
        ("y", "control"),
        ("z", "control"),
    ]:
        for d in dates:
            shock = 0.0
            if regional_shock:
                for e in EVENTS:
                    rel = (d - e).days
                    if -5 <= rel <= 0:
                        shock += 0.5  # bad spell before the order, hits every city
            treat = effect if role == "grap" and any(0 < (d - e).days <= 7 for e in EVENTS) else 0
            log_ratio = shock + treat + rng.normal(0, 0.02)
            rows.append(
                {
                    "city": city,
                    "date": d,
                    "city_role": role,
                    "log_ratio": log_ratio,
                    "log_raw": log_ratio + 5,
                    "days_from_diwali": 100,
                }
            )
    return pd.DataFrame(rows)


def test_regional_spell_fools_the_naive_estimate_but_not_the_comparison():
    panel = make_panel(effect=0.0)
    steps = ge.three_steps(panel, EVENTS)
    assert steps[1].effect_pct < -15  # weather-adjusted alone sees a big fake "drop"
    assert steps[2].effect_pct == pytest.approx(0, abs=2)  # the comparison cancels it


def test_comparison_finds_a_real_30_percent_cut():
    panel = make_panel(effect=np.log(0.7))
    assert ge.three_steps(panel, EVENTS)[2].effect_pct == pytest.approx(-30, abs=3)


def test_find_events_on_and_off():
    stages = pd.DataFrame(
        {"date": pd.date_range("2025-11-01", periods=6), "grap_stage": [2, 3, 4, 3, 2, 2]}
    )
    assert ge.find_events(stages, 3, "on") == [pd.Timestamp("2025-11-02")]
    assert ge.find_events(stages, 3, "off") == [pd.Timestamp("2025-11-05")]


def test_pct_reads_log_changes_as_percent():
    assert ge.pct(np.log(0.9)) == pytest.approx(-10)


def test_synthetic_control_weights_recover_the_mix():
    rng = np.random.default_rng(0)
    donors = rng.normal(0, 1, (60, 4))
    target = donors @ np.array([0.6, 0.4, 0.0, 0.0])
    w = ge.synth_weights(target, donors)
    assert w.round(2).tolist() == [0.6, 0.4, 0.0, 0.0]


def test_quiet_days_skip_any_window_with_a_stage_change():
    dates = pd.date_range("2025-11-01", "2025-12-31", freq="D")
    stage = np.where(dates < pd.Timestamp("2025-12-01"), 2, 3)
    stages = pd.DataFrame({"date": dates, "grap_stage": stage})
    panel = pd.DataFrame({"date": dates, "city_role": "grap"})
    quiet = ge.quiet_days(stages, panel)
    # the stage changes between 30 Nov and 1 Dec, so any day from 24 Nov to 7 Dec
    # has that change inside its 7-days-either-side window
    near = [d for d in quiet if -7 <= (d - pd.Timestamp("2025-12-01")).days <= 6]
    assert near == []
    assert pd.Timestamp("2025-12-08") in quiet
    assert pd.Timestamp("2025-11-15") in quiet
