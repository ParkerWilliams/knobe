"""WO-8 §3: descriptive figures -- per-cell DISTRIBUTIONS (not just means),
item-level caterpillar plots, and model-family comparison panels. Every figure
is drawn through ``analysis/figstyle.py`` (one palette, one savefig, Agg
backend). Item means used here are for DESCRIPTION ONLY -- inference never
aggregates response-level ratings (master spec §6.3); that rule lives in
``analysis/models.py``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from knobe.analysis import figstyle


def _item_means_ci(df: pd.DataFrame, group_col: str = "variant_id") -> pd.DataFrame:
    """Per-item mean rating + a normal-approx 95% CI half-width (descriptive
    only). Returns one row per item with mean, ci, n, and the item's valence."""
    g = df.groupby(group_col)
    means = g["rating"].mean()
    sds = g["rating"].std(ddof=1).fillna(0.0)
    ns = g["rating"].count()
    ci = 1.96 * sds / np.sqrt(ns.clip(lower=1))
    valence = g["valence"].first()
    sign = g["sign"].first()
    out = pd.DataFrame({"mean": means, "ci": ci, "n": ns, "valence": valence, "sign": sign})
    return out.reset_index()


def per_cell_distribution(
    df: pd.DataFrame, out_path: str | Path, *, question_type: str = "intentionality",
) -> Path:
    """Per-valence-cell distribution of intentionality ratings (a violin +
    overlaid ECDF-style strip via the raw points is overkill for the toy;
    a violin per valence cell IS the distribution, not just the mean -- WO-8
    §3's requirement). One panel, valence on x."""
    plt = figstyle._pyplot()
    sub = df[df["question_type"] == question_type]
    fig, ax = figstyle.new_axes()
    order = ["MB", "MG", "NMB", "NMG", "NEU"]
    present = [v for v in order if v in set(sub["valence"])]
    data = [sub.loc[sub["valence"] == v, "rating"].to_numpy() for v in present]
    if any(len(d) > 0 for d in data):
        parts = ax.violinplot(data, showmeans=True, showextrema=False)
        for i, body in enumerate(parts["bodies"]):
            valence = present[i]
            role = {"MB": "bad", "NMB": "bad", "MG": "good", "NMG": "good", "NEU": "neutral"}[valence]
            body.set_facecolor(figstyle.color_for(role))
            body.set_alpha(0.6)
    ax.set_xticks(range(1, len(present) + 1))
    ax.set_xticklabels(present)
    ax.set_ylabel(f"{question_type} rating (0-10)")
    ax.set_xlabel("valence cell")
    ax.set_title(f"Per-cell {question_type} distribution")
    return figstyle.savefig(fig, out_path)


def item_caterpillar(
    df: pd.DataFrame, out_path: str | Path, *, question_type: str = "intentionality",
) -> Path:
    """Item-level caterpillar plot: each item's mean +/- 95% CI, sorted by
    mean (WO-8 §3). Colour by sign (bad/good/neutral)."""
    sub = df[df["question_type"] == question_type]
    stats = _item_means_ci(sub).sort_values("mean").reset_index(drop=True)
    fig, ax = figstyle.new_axes(figsize=(7.0, max(3.0, 0.18 * len(stats) + 1.0)))
    ys = np.arange(len(stats))
    role_map = {"bad": "bad", "good": "good", "na": "neutral"}
    colors = [figstyle.color_for(role_map.get(s, "neutral")) for s in stats["sign"]]
    ax.errorbar(
        stats["mean"], ys, xerr=stats["ci"], fmt="o", markersize=3, linewidth=0.8,
        ecolor=figstyle.PALETTE["grid"], mfc="none",
    )
    for x, y, c in zip(stats["mean"], ys, colors):
        ax.plot([x], [y], "o", markersize=4, color=c)
    ax.set_yticks([])
    ax.set_xlabel(f"item mean {question_type} rating (+/- 95% CI)")
    ax.set_title(f"Item caterpillar ({question_type}, n={len(stats)} items)")
    return figstyle.savefig(fig, out_path)


def model_family_panel(
    df: pd.DataFrame, out_path: str | Path, *, question_type: str = "intentionality",
) -> Path:
    """Model-family comparison panel (WO-8 §3): the bad-minus-good
    intentionality gap per model_family x tuning_status -- the headline RQ1
    quantity, descriptively, so families/checkpoints can be compared at a
    glance."""
    sub = df[(df["question_type"] == question_type) & (df["sign"].isin(["bad", "good"]))]
    fig, ax = figstyle.new_axes()
    families = sorted(sub["model_family"].unique())
    width = 0.38
    xs = np.arange(len(families))
    for offset, tuning in ((-width / 2, "pretrained"), (width / 2, "finetuned")):
        gaps = []
        for fam in families:
            cell = sub[(sub["model_family"] == fam) & (sub["tuning_status"] == tuning)]
            bad = cell.loc[cell["sign"] == "bad", "rating"].mean()
            good = cell.loc[cell["sign"] == "good", "rating"].mean()
            gaps.append((bad - good) if np.isfinite(bad) and np.isfinite(good) else 0.0)
        ax.bar(xs + offset, gaps, width, label=tuning, color=figstyle.color_for(tuning))
    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_xticks(xs)
    ax.set_xticklabels(families, rotation=20, ha="right")
    ax.set_ylabel("bad - good mean intentionality gap")
    ax.set_title("Model-family comparison: Knobe gap by checkpoint")
    ax.legend(fontsize="small")
    return figstyle.savefig(fig, out_path)


def generate_all(df: pd.DataFrame, out_dir: str | Path) -> list[Path]:
    """Draws the standard figure set into ``out_dir`` and returns the saved
    paths (skipping any that have no data to draw)."""
    out_dir = Path(out_dir)
    paths: list[Path] = []
    if df.empty:
        return paths
    paths.append(per_cell_distribution(df, out_dir / "per_cell_distribution.png"))
    paths.append(item_caterpillar(df, out_dir / "item_caterpillar.png"))
    if df["model_family"].nunique() >= 1:
        paths.append(model_family_panel(df, out_dir / "model_family_panel.png"))
    return paths
