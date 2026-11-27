"""Charts for Part 7."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from breathe_check.analysis import style


def plot_three_steps(on: list, off: list):
    """Dot-and-range chart: how the estimate changes as each trap is removed."""
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    labels = [
        "Raw before vs after",
        "Weather taken out",
        "Weather out, vs cities\nwithout GRAP",
    ]
    y = np.arange(len(labels))[::-1]
    for offset, (color, name, ests) in zip(
        (0.14, -0.14),
        (
            (style.SERIES[0], "Stage III/IV switched on", on),
            (style.SERIES[1], "Stage III/IV switched off", off),
        ),
        strict=True,
    ):
        for yi, e in zip(y, ests, strict=True):
            ax.hlines(yi + offset, e.low_pct, e.high_pct, color=color, linewidth=2, alpha=0.55)
            ax.plot(
                e.effect_pct,
                yi + offset,
                "o",
                color=color,
                markersize=8,
                markeredgecolor=style.SURFACE,
                markeredgewidth=1.5,
            )
            ax.annotate(
                f"{e.effect_pct:+.0f}%",
                (e.effect_pct, yi + offset),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=style.TEXT,
            )
        ax.plot([], [], "o", color=color, label=name)
    ax.axvline(0, color=style.TEXT_MUTED, linewidth=1)
    ax.set_yticks(y, labels)
    ax.grid(axis="x", color=style.GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Change in PM2.5, week after vs week before (%). Lines show the 90% range.")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(
        "Once weather and the region are accounted for, the 'effect' mostly vanishes", pad=22
    )
    style.subtitle(
        ax,
        "Delhi-NCR, the 4 times Stage III/IV was switched on and the 4 times it was switched off.",
    )
    style.source_note(fig, "Data: CPCB via OpenAQ, Open-Meteo, CAQM orders. Breathe Check.")
    return fig


def plot_event_study(study: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    s = study.sort_values("rel_day")
    ax.fill_between(
        s["rel_day"], s["low_pct"], s["high_pct"], color=style.SERIES[0], alpha=0.15, linewidth=0
    )
    ax.plot(s["rel_day"], s["effect_pct"], color=style.SERIES[0], marker="o", markersize=4)
    ax.axhline(0, color=style.TEXT_MUTED, linewidth=1)
    ax.axvline(0, color=style.TEXT_MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(
        0.15,
        ax.get_ylim()[1] * 0.92,
        "Stage III/IV\nswitched on",
        fontsize=9,
        color=style.TEXT_SECONDARY,
        va="top",
    )
    ax.set_xticks(range(-7, 8))
    ax.set_xlabel("Days from the order")
    ax.set_ylabel("Delhi-NCR vs non-GRAP cities (%)\nweather taken out")
    ax.set_title(
        "Delhi-NCR was pulling ahead of other cities before the orders, and stayed there", pad=22
    )
    style.subtitle(
        ax, "Gap relative to the week before. Shaded: 90% range. Only 4 events, so it's wide."
    )
    style.source_note(fig, "Data: CPCB via OpenAQ, Open-Meteo, CAQM orders. Breathe Check.")
    return fig


def plot_placebo(fake: np.ndarray, real: float):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.hist(
        fake,
        bins=40,
        color=style.SERIES[1],
        alpha=0.75,
        edgecolor=style.SURFACE,
        linewidth=0.8,
        zorder=3,
    )
    ax.axvline(real, color=style.SERIES[0], linewidth=2.5, zorder=4)
    ax.annotate(
        f"Real GRAP\nestimate: {real:+.0f}%",
        (real, ax.get_ylim()[1] * 0.9),
        xytext=(8, 0),
        textcoords="offset points",
        fontsize=9.5,
        color=style.TEXT,
        va="top",
    )
    share = float((np.abs(fake) >= abs(real)).mean())
    ax.set_xlabel("Estimated 'effect' (%) on fake dates when no stage changed")
    ax.set_ylabel("How often")
    ax.set_title("The real result looks just like what random dates give", pad=22)
    style.subtitle(
        ax,
        f"{len(fake):,} draws of 4 quiet winter days. "
        f"{share:.0%} are at least as big as the real one.",
    )
    style.source_note(fig, "Data: CPCB via OpenAQ, Open-Meteo, CAQM orders. Breathe Check.")
    return fig
