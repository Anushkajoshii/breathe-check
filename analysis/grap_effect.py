"""Part 7: did GRAP work? Prints every number used in reports/03-did-grap-work.md.

uv run python analysis/grap_effect.py
"""

import pandas as pd

from breathe_check import grap, settings
from breathe_check.analysis import grap_charts as charts
from breathe_check.analysis import grap_effect as ge
from breathe_check.analysis import style
from breathe_check.analysis.load import load

DATA_START = "2025-02-19"


def show(title, estimates):
    print(f"\n== {title}")
    for e in estimates:
        print(
            f"  {e.label:48s} {e.effect_pct:+6.1f}%  "
            f"(90% range {e.low_pct:+.1f} to {e.high_pct:+.1f}), {e.events} events"
        )


def main() -> None:
    style.setup()
    panel = ge.build_panel(load("city_day_adjusted"), load("city_day"))
    stages = grap.daily_stage()
    sure = stages[["date", "grap_stage"]].copy()
    sure["grap_stage"] = (
        grap.daily_stage(grap.load_orders().query("needs_review == 'no'").reset_index(drop=True))
        .set_index("date")
        .reindex(stages["date"])["grap_stage"]
        .values
    )

    heavy_on = ge.find_events(stages, 3, "on", start=DATA_START)
    heavy_off = ge.find_events(stages, 3, "off", start=DATA_START)
    any_on = ge.find_events(stages, 1, "on", start=DATA_START)
    print("Stage III+ on: ", [d.date().isoformat() for d in heavy_on])
    print("Stage III+ off:", [d.date().isoformat() for d in heavy_off])
    print("Stage I on:    ", len(any_on), "events")

    show("Stage III or IV switched ON", ge.three_steps(panel, heavy_on))
    show("Stage III or IV switched OFF", ge.three_steps(panel, heavy_off))
    show("Stage I switched ON (mild measures)", ge.three_steps(panel, any_on))

    # robustness
    show("ON, counting from the day after the order", ge.three_steps(panel, heavy_on, shift_days=1))
    sure_on = ge.find_events(sure, 3, "on", start=DATA_START)
    show(f"ON, sure-only dates ({len(sure_on)} events)", ge.three_steps(panel, sure_on))
    no_diwali = panel[~panel["days_from_diwali"].between(-3, 7)]
    show("ON, leaving out Diwali week", ge.three_steps(no_diwali, heavy_on))

    study = ge.event_study(panel, heavy_on)
    study_off = ge.event_study(panel, heavy_off)
    print("\nEvent study, ON:\n", study.round(1).to_string(index=False))

    fake = ge.placebo(panel, stages, n_events=len(heavy_on))
    real = ge.three_steps(panel, heavy_on)[2].effect_pct
    share = (abs(fake) >= abs(real)).mean()
    low, high = pd.Series(fake).quantile([0.05, 0.95])
    print(
        f"\nPlacebo: {len(fake)} sets of {len(heavy_on)} fake events. "
        f"Middle 90%: {low:+.1f} to {high:+.1f}%. Share as big as the real one: {share:.0%}"
    )

    synth = [ge.synthetic_control(panel, e) for e in heavy_on]
    synth = pd.DataFrame([s for s in synth if s])
    print("\nSynthetic control, Delhi:\n", synth.to_string(index=False))

    print(
        style.save(
            charts.plot_three_steps(
                ge.three_steps(panel, heavy_on), ge.three_steps(panel, heavy_off)
            ),
            "10_grap_three_steps",
        )
    )
    print(style.save(charts.plot_event_study(study), "11_grap_event_study"))
    print(style.save(charts.plot_placebo(fake, real), "12_grap_placebo"))

    out = {
        "study_on": study,
        "study_off": study_off,
        "placebo": pd.DataFrame({"effect_pct": fake}),
        "synth": synth,
    }
    for name, frame in out.items():
        frame.to_parquet(settings.DATA_DIR / "clean" / f"grap_{name}.parquet", index=False)


if __name__ == "__main__":
    main()
