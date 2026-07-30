"""WO-8 §3: the single figure-styling module. Every figure in
``analysis/figures.py`` goes through here -- one Agg backend selection, one
palette, one savefig helper -- so the paper's figures read as one system and
nothing imports matplotlib directly at analysis-module import time (it stays a
lazy, guarded import behind the 'stats' extra, per common-context.md
constraint 7).
"""
from __future__ import annotations

from pathlib import Path


def _pyplot():
    """Lazy, guarded matplotlib import with the non-interactive Agg backend
    forced (headless H200/laptop/CI -- no display). Raises a clear install
    hint rather than a bare ImportError."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover -- only without the 'stats' extra
        raise RuntimeError(
            "matplotlib is required for analysis figures -- install the 'stats' extra "
            "(`uv pip install -e '.[stats]'`)."
        ) from exc
    return plt


# Consistent, colour-blind-safe palette used everywhere in the paper figures.
# Keyed by the semantic roles the RQ1 figures actually draw.
PALETTE = {
    "bad": "#d1495b",
    "good": "#30638e",
    "moral": "#3c1642",
    "nonmoral": "#048ba8",
    "neutral": "#8d99ae",
    "pretrained": "#8d99ae",
    "finetuned": "#e07a5f",
    "accent": "#0b6e4f",
    "grid": "#cccccc",
}
DEFAULT_COLOR = "#333333"


def color_for(key: str) -> str:
    return PALETTE.get(key, DEFAULT_COLOR)


def new_axes(figsize: tuple[float, float] = (7.0, 4.5)):
    """One styled (fig, ax) -- the only place figure defaults live."""
    plt = _pyplot()
    fig, ax = plt.subplots(figsize=figsize)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", color=PALETTE["grid"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    return fig, ax


def savefig(fig, out_path: str | Path) -> Path:
    """Saves ``fig`` to ``out_path`` (parent dirs created) at a consistent DPI
    and closes it -- the one savefig path, so no figure leaks an open handle."""
    plt = _pyplot()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
