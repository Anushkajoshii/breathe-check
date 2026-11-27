"""Part 7: did GRAP work?

The trap. GRAP stages are switched on *because* the air is unusually bad. Bad
spells end on their own: the wind returns, a cold snap passes. So PM2.5 almost
always falls after a stage is switched on, rule or no rule ("regression to the
mean"). A simple before/after makes any rule look like it works.

How we get around it, step by step:
1. Naive: raw PM2.5, the week after vs the week before. (Shown to make the trap visible.)
2. Weather-adjusted: same, but on actual / what-the-weather-predicts (Part 6).
3. Compared with cities without GRAP: Delhi-NCR's weather-adjusted change minus
   the change in Lucknow, Kanpur, Patna and Chandigarh over the same days.
   These cities share the Indo-Gangetic plain's winters, smoke and festivals,
   but not GRAP. A regional bad spell that clears hits both groups, so it cancels.
   This is a difference-in-differences.
4. Checks: synthetic control (a weighted mix of non-GRAP cities built to track
   Delhi before each event), placebo dates with no stage change, and re-running
   without the unclear GRAP dates, with a one-day delay, and without Diwali.

Everything is on the log scale, so results read as percentages.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

PRE = range(-7, 0)  # the week before (day 0 is the order date)
POST = range(1, 8)  # the week after, from the first full day
WINDOW = range(-7, 8)


def pct(log_change: float) -> float:
    """A change on the log scale as a percentage: -0.105 -> -10.0."""
    return (np.exp(log_change) - 1) * 100


# ---------- data ----------


def build_panel(adjusted: pd.DataFrame, city_day: pd.DataFrame) -> pd.DataFrame:
    """One row per city per day with raw and weather-adjusted log PM2.5."""
    keep = [
        "city",
        "date",
        "city_role",
        "grap_stage",
        "grap_stage_sure_only",
        "days_from_diwali",
        "fires_confident_yesterday",
    ]
    cd = city_day[keep].copy()
    cd["date"] = pd.to_datetime(cd["date"])
    adj = adjusted.copy()
    adj["date"] = pd.to_datetime(adj["date"])
    panel = adj.merge(cd, on=["city", "date"], how="inner")
    panel["log_raw"] = np.log(panel["pm25"])
    panel["log_ratio"] = np.log(panel["ratio"])
    return panel


def find_events(stages: pd.DataFrame, level: int, direction: str, start=None, end=None) -> list:
    """Days when the highest stage crossed `level`.

    direction "on":  from below `level` to `level` or above (e.g. Stage III switched on)
    direction "off": from `level` or above to below it
    """
    s = stages.sort_values("date").copy()
    s["date"] = pd.to_datetime(s["date"])
    prev = s["grap_stage"].shift(1)
    if direction == "on":
        hit = (prev < level) & (s["grap_stage"] >= level)
    else:
        hit = (prev >= level) & (s["grap_stage"] < level)
    dates = s.loc[hit, "date"]
    if start is not None:
        dates = dates[dates >= pd.Timestamp(start)]
    if end is not None:
        dates = dates[dates <= pd.Timestamp(end)]
    return list(dates)


# ---------- event windows ----------


def event_table(
    panel: pd.DataFrame, events: list, column: str, shift_days: int = 0
) -> pd.DataFrame:
    """For each event and each day from -7 to +7: the GRAP group's average and the
    comparison group's average of `column`."""
    rows = []
    for event in events:
        start = pd.Timestamp(event) + pd.Timedelta(days=shift_days)
        for rel in WINDOW:
            day = start + pd.Timedelta(days=rel)
            today = panel[panel["date"] == day]
            treated = today.loc[today["city_role"] == "grap", column].mean()
            control = today.loc[today["city_role"] == "control", column].mean()
            rows.append({"event": start, "rel_day": rel, "treated": treated, "control": control})
    t = pd.DataFrame(rows)
    t["gap"] = t["treated"] - t["control"]
    return t


def before_after(table: pd.DataFrame, value: str) -> pd.Series:
    """Per event: average of `value` in the week after minus the week before."""
    pre = table[table["rel_day"].isin(PRE)].groupby("event")[value].mean()
    post = table[table["rel_day"].isin(POST)].groupby("event")[value].mean()
    return (post - pre).dropna()


def bootstrap_mean(values: np.ndarray, n: int = 5000, seed: int = 0) -> tuple[float, float, float]:
    """Mean with a 90% range from resampling the events themselves."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(n, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), float(np.percentile(draws, 5)), float(np.percentile(draws, 95))


@dataclass
class Estimate:
    label: str
    events: int
    effect_pct: float
    low_pct: float
    high_pct: float


def estimate(label: str, changes: pd.Series) -> Estimate:
    mean, low, high = bootstrap_mean(changes.values)
    return Estimate(label, len(changes), pct(mean), pct(low), pct(high))


def three_steps(panel: pd.DataFrame, events: list, shift_days: int = 0) -> list[Estimate]:
    """The naive, weather-adjusted and compared-with-other-cities estimates."""
    raw = event_table(panel, events, "log_raw", shift_days)
    adj = event_table(panel, events, "log_ratio", shift_days)
    return [
        estimate("1. Before vs after (raw PM2.5)", before_after(raw, "treated")),
        estimate("2. Weather taken out", before_after(adj, "treated")),
        estimate("3. Weather out, compared with non-GRAP cities", before_after(adj, "gap")),
    ]


def event_study(panel: pd.DataFrame, events: list, column: str = "log_ratio") -> pd.DataFrame:
    """Average gap (GRAP minus comparison cities) on each day, relative to the week
    before, with a 90% range from resampling events."""
    t = event_table(panel, events, column)
    base = t[t["rel_day"].isin(PRE)].groupby("event")["gap"].mean()
    t["gap_vs_before"] = t["gap"] - t["event"].map(base)
    rows = []
    for rel, part in t.groupby("rel_day"):
        vals = part["gap_vs_before"].dropna().values
        mean, low, high = bootstrap_mean(vals) if len(vals) else (np.nan,) * 3
        rows.append(
            {
                "rel_day": rel,
                "effect_pct": pct(mean),
                "low_pct": pct(low),
                "high_pct": pct(high),
                "events": len(vals),
            }
        )
    return pd.DataFrame(rows)


# ---------- placebo dates ----------


def quiet_days(stages: pd.DataFrame, panel: pd.DataFrame, months=(10, 11, 12, 1, 2)) -> list:
    """Winter days in the data with no change in GRAP stage for 7 days either side."""
    s = stages.copy()
    s["date"] = pd.to_datetime(s["date"])
    s = s.set_index("date")["grap_stage"]
    have = set(panel.loc[panel["city_role"] == "grap", "date"])
    out = []
    for day in s.index:
        if day.month not in months or day not in have:
            continue
        around = s.loc[day - pd.Timedelta(days=7) : day + pd.Timedelta(days=7)]
        if len(around) == 15 and around.nunique() == 1:
            out.append(day)
    return out


def placebo(
    panel: pd.DataFrame, stages: pd.DataFrame, n_events: int, draws: int = 2000, seed: int = 1
) -> np.ndarray:
    """Pretend GRAP switched on at random quiet winter days. Returns the
    step-3 estimate (in %) for each draw of `n_events` fake events."""
    days = quiet_days(stages, panel)
    adj = event_table(panel, days, "log_ratio")
    per_day = before_after(adj, "gap")
    rng = np.random.default_rng(seed)
    picks = rng.choice(per_day.values, size=(draws, n_events), replace=True)
    return pct(picks.mean(axis=1))


# ---------- synthetic control ----------


def synth_weights(target: np.ndarray, donors: np.ndarray) -> np.ndarray:
    """Non-negative weights that add up to 1 and make the donors' weighted
    average track the target as closely as possible."""
    k = donors.shape[1]

    def loss(w):
        return np.mean((target - donors @ w) ** 2)

    res = minimize(
        loss,
        np.full(k, 1 / k),
        method="SLSQP",
        bounds=[(0, 1)] * k,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
    )
    return res.x


def synthetic_control(
    panel: pd.DataFrame,
    event,
    treated_city: str = "delhi",
    fit_days: int = 45,
    column: str = "log_ratio",
) -> dict | None:
    """Delhi vs a weighted mix of non-GRAP cities fitted on the 45 days before."""
    event = pd.Timestamp(event)
    wide = panel.pivot_table(index="date", columns="city", values=column)
    roles = panel.drop_duplicates("city").set_index("city")["city_role"]
    donors = [c for c in wide.columns if roles[c] != "grap"]
    fit = wide.loc[event - pd.Timedelta(days=fit_days) : event - pd.Timedelta(days=1)]
    after = wide.loc[event + pd.Timedelta(days=1) : event + pd.Timedelta(days=7)]
    fit = fit.dropna(subset=[treated_city])
    donors = [c for c in donors if fit[c].notna().mean() > 0.9 and after[c].notna().all()]
    fit = fit[[treated_city, *donors]].dropna()
    if len(fit) < 20 or after[treated_city].isna().any() or len(donors) < 3:
        return None
    w = synth_weights(fit[treated_city].values, fit[donors].values)
    synth_after = after[donors].values @ w
    synth_fit = fit[donors].values @ w
    pre_gap = float(np.mean(fit[treated_city].values - synth_fit))
    post_gap = float(np.mean(after[treated_city].values - synth_after))
    pre_rmse = float(np.sqrt(np.mean((fit[treated_city].values - synth_fit) ** 2)))
    top = sorted(zip(donors, w, strict=True), key=lambda x: -x[1])[:3]
    return {
        "event": event,
        "effect_pct": pct(post_gap - pre_gap),
        "pre_fit_error_pct": pct(pre_rmse),
        "main_donors": ", ".join(f"{c} {wt:.0%}" for c, wt in top if wt > 0.05),
    }
