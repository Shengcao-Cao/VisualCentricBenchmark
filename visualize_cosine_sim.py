#!/usr/bin/env python3
"""Visualize the pairwise cosine similarity distribution.

Only considers cross-dataset pairs (excludes pairs within the same data source).

Run from the coreset directory:
    python visualize_cosine_sim.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

BG_COLOR = "#FAFAFA"
GRID_COLOR = "#E0E0E0"
OUT = Path("vis_dedup")
OUT.mkdir(exist_ok=True)

d = np.load("cosine_sim.npz", allow_pickle=True)
sim = d["cosine_sim"]
ids = d["ids"]
n = sim.shape[0]

# Load dataset labels and build cross-dataset mask
data = {item["id"]: item for item in json.load(open("all_data.json"))}
datasets = np.array([data[str(id_)]["dataset"] for id_ in ids])
ri, ci = np.triu_indices(n, k=1)
cross_mask = datasets[ri] != datasets[ci]
upper = sim[ri, ci][cross_mask]
print(f"Total upper-triangle pairs: {len(ri):,}, cross-dataset: {cross_mask.sum():,}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor(BG_COLOR)

# --- Left: full distribution ---
ax = axes[0]
ax.set_facecolor(BG_COLOR)
ax.hist(upper, bins=200, color="#4C72B0", edgecolor="none", alpha=0.85)
ax.set_xlabel("Cosine Similarity", fontsize=11)
ax.set_ylabel("Number of Pairs (log scale)", fontsize=11)
ax.set_yscale("log")
ax.set_title("Pairwise Cosine Similarity Distribution", fontsize=14, fontweight="bold")
ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

# Add vertical lines for thresholds
for t, color, label in [
    (0.9, "#DD8452", "0.9"),
    (0.95, "#C44E52", "0.95"),
    (0.99, "#8B0000", "0.99"),
]:
    count = (upper > t).sum()
    ax.axvline(t, color=color, linestyle="--", linewidth=1.2, alpha=0.8)
    ax.text(
        t + 0.003,
        ax.get_ylim()[1] * 0.5,
        f">{label}\n({count:,})",
        fontsize=8,
        color=color,
        fontweight="bold",
        va="center",
    )

# --- Right: zoomed into high-similarity tail ---
ax = axes[1]
ax.set_facecolor(BG_COLOR)
tail = upper[upper > 0.8]
ax.hist(tail, bins=200, color="#C44E52", edgecolor="none", alpha=0.85)
ax.set_xlabel("Cosine Similarity", fontsize=11)
ax.set_ylabel("Number of Pairs", fontsize=11)
ax.set_title("High Similarity Tail (> 0.8)", fontsize=14, fontweight="bold")
ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

# Annotate key stats
stats_text = (
    f"Total pairs: {len(upper):,}\n"
    f"Mean: {upper.mean():.4f}\n"
    f"Median: {np.median(upper):.4f}\n"
    f"> 0.9: {(upper > 0.9).sum():,}\n"
    f"> 0.95: {(upper > 0.95).sum():,}\n"
    f"> 0.99: {(upper > 0.99).sum():,}"
)
ax.text(
    0.97,
    0.95,
    stats_text,
    transform=ax.transAxes,
    fontsize=9,
    va="top",
    ha="right",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="#CCCCCC"),
    family="monospace",
)

fig.tight_layout()
fig.savefig(OUT / "cosine_similarity.png", dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
plt.close(fig)
print(f"Saved {OUT / 'cosine_similarity.png'}")
