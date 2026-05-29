#!/usr/bin/env python3
"""Two side-by-side pie charts: domain distribution and question-type distribution."""

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "filtered_data_with_solution_hard.json"
OUT_DIR = Path(__file__).resolve().parent

BG_COLOR = "#FFFFFF"
LABEL_SIZE = 9
PCT_SIZE = 8

DOMAIN_COLORS = {
    "Math": "#4C72B0",
    "Physics": "#DD8452",
    "Chemistry": "#55A868",
    "Biology": "#937860",
    "Geography": "#DA8BC3",
    "Puzzle": "#C44E52",
    "Computer Science": "#8172B3",
    "Engineering": "#CCB974",
}

DOMAIN_ORDER = ["Math", "Physics", "Chemistry", "Biology", "Geography", "Puzzle", "Computer Science", "Engineering"]

QTYPE_COLORS = {
    "free_form": "#4C72B0",
    "single_selection": "#55A868",
    "multiple_selection": "#DD8452",
}
QTYPE_ORDER = ["free_form", "single_selection", "multiple_selection"]
QTYPE_LABELS = {
    "free_form": "Free-form",
    "single_selection": "Single Selection",
    "multiple_selection": "Multiple Selection",
}


def make_pie(ax, labels, sizes, colors, min_pct=4.0, label_offsets=None):
    """label_offsets: dict mapping label -> angle offset in degrees for the outside text."""
    total = sum(sizes)
    if label_offsets is None:
        label_offsets = {}
    wedges, _ = ax.pie(
        sizes,
        labels=None,
        colors=colors,
        explode=[0.02] * len(labels),
        startangle=90,
    )

    for wedge, label, size in zip(wedges, labels, sizes):
        pct = size / total * 100
        if pct < min_pct:
            continue
        ang = (wedge.theta2 + wedge.theta1) / 2
        label_ang = ang + label_offsets.get(label, 0)
        rad = np.deg2rad(ang)
        label_rad = np.deg2rad(label_ang)
        # label outside (use adjusted angle), percentage inside (use true angle)
        x_out = 1.18 * np.cos(label_rad)
        y_out = 1.18 * np.sin(label_rad)
        ha = "left" if x_out >= 0 else "right"
        ax.text(
            x_out, y_out, f"{label}\n({size:,})",
            ha=ha, va="center", fontsize=LABEL_SIZE, fontweight="medium",
        )
        x_in = 0.65 * np.cos(rad)
        y_in = 0.65 * np.sin(rad)
        ax.text(
            x_in, y_in, f"{pct:.1f}%",
            ha="center", va="center", fontsize=PCT_SIZE,
            fontweight="bold", color="white",
        )


def main():
    with open(DATA_PATH) as f:
        items = json.load(f)
    print(f"Loaded {len(items):,} items")

    domains = Counter(it["domain"] for it in items)
    qtypes = Counter(it["question_type"] for it in items)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.5, 2.4))
    fig.patch.set_facecolor(BG_COLOR)

    # Left: domain
    dom_labels = [d for d in DOMAIN_ORDER if d in domains]
    dom_sizes = [domains[d] for d in dom_labels]
    dom_colors = [DOMAIN_COLORS[d] for d in dom_labels]
    make_pie(ax1, dom_labels, dom_sizes, dom_colors,
             label_offsets={"Biology": 0, "Geography": 10})
    # Right: question type
    qt_labels_raw = [q for q in QTYPE_ORDER if q in qtypes]
    qt_sizes = [qtypes[q] for q in qt_labels_raw]
    qt_colors = [QTYPE_COLORS[q] for q in qt_labels_raw]
    qt_labels = [QTYPE_LABELS[q] for q in qt_labels_raw]
    make_pie(ax2, qt_labels, qt_sizes, qt_colors,
             label_offsets={"Free-form": 30})

    fig.subplots_adjust(wspace=0.3)

    for fmt in ("pdf", "png"):
        out = OUT_DIR / f"distribution.{fmt}"
        fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"  -> {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
