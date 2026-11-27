"""One chart style for the whole project, so every figure reads the same way.

Colours come from a palette checked for colour-blind safety (at most three
series per chart; the third colour is light, so every line is labelled
directly). Limits are drawn as grey dashed lines with a label, never as colour.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8985"
GRID = "#e6e5e1"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")  # blue, orange, aqua

FIGURES = Path(__file__).resolve().parents[3] / "reports" / "figures"


def setup() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlecolor": TEXT,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "ytick.left": False,
            "lines.linewidth": 2,
            "lines.solid_capstyle": "round",
            "font.size": 10,
            "legend.frameon": False,
            "figure.dpi": 110,
            "savefig.dpi": 160,
            "savefig.bbox": "tight",
        }
    )


def subtitle(ax, text: str) -> None:
    """A one-line plain-language takeaway under the title."""
    ax.text(0, 1.02, text, transform=ax.transAxes, color=TEXT_SECONDARY, fontsize=10, va="bottom")


def limit_line(ax, y: float, label: str) -> None:
    """A grey dashed reference line, labelled just above it at the left edge."""
    ax.axhline(y, color=TEXT_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate(
        label,
        (0, y),
        xycoords=("axes fraction", "data"),
        xytext=(4, 3),
        textcoords="offset points",
        color=TEXT_SECONDARY,
        fontsize=8.5,
        va="bottom",
    )


def end_label(ax, x, y, text: str, color: str) -> None:
    """Label a line at its right end, in text ink with a colour dot for identity."""
    ax.plot([x], [y], marker="o", markersize=5, color=color, zorder=4, clip_on=False)
    ax.annotate(
        text,
        (x, y),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=9.5,
        color=TEXT,
        annotation_clip=False,
    )


def source_note(
    fig, text: str = "Data: CPCB via OpenAQ, Open-Meteo, NASA FIRMS. Breathe Check."
) -> None:
    fig.text(0.01, -0.02, text, color=TEXT_MUTED, fontsize=8, ha="left", va="top")


def save(fig, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path
