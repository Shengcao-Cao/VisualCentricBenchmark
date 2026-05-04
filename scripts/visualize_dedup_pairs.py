#!/usr/bin/env python3
"""Visualize example pairs at different cosine similarity levels.

Run from the coreset directory:
    python visualize_dedup_pairs.py
"""

import json
import re
import textwrap
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

OUT = Path("vis_dedup")
OUT.mkdir(exist_ok=True)

BG_COLOR = "#FAFAFA"

# Find a CJK-capable font
CJK_FONT = None
for candidate in [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]:
    if Path(candidate).exists():
        CJK_FONT = candidate
        break

if CJK_FONT:
    prop = fm.FontProperties(fname=CJK_FONT)
    prop_bold = fm.FontProperties(fname=CJK_FONT, weight="bold")
    print(f"Using CJK font: {CJK_FONT}")
else:
    prop = fm.FontProperties()
    prop_bold = fm.FontProperties(weight="bold")
    print("Warning: no CJK font found")

sim_data = np.load("cosine_sim.npz", allow_pickle=True)
ids = sim_data["ids"]
cosine = sim_data["cosine_sim"]
data = {d["id"]: d for d in json.load(open("all_data.json"))}

n = len(ids)
ri, ci = np.triu_indices(n, k=1)
all_vals = cosine[ri, ci]

# Only keep cross-dataset pairs (exclude pairs within the same data source)
datasets = np.array([data[str(id_)]["dataset"] for id_ in ids])
cross_mask = datasets[ri] != datasets[ci]
ri = ri[cross_mask]
ci = ci[cross_mask]
vals = all_vals[cross_mask]
print(f"Cross-dataset pairs: {len(vals):,} (excluded {(~cross_mask).sum():,} same-dataset pairs)")


def get_first_image(item):
    indices = re.findall(r"<image_(\d+)>", item["question"])
    imgs = item.get("images", [])
    if indices and imgs:
        idx = int(indices[0]) - 1
        if 0 <= idx < len(imgs):
            path = Path(imgs[idx])
            if path.exists():
                return Image.open(path)
    return None


def clean_question(text, max_len=250):
    text = re.sub(r"<image_\d+>", "[IMG]", text).strip()
    # Strip LaTeX $ delimiters to avoid math-mode font issues
    text = text.replace("$", "")
    # Collapse multiple whitespace/newlines
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def draw_item(ax, item, item_id, label, img):
    """Draw one item (text + image) vertically in a single axes."""
    ax.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("#DDDDDD")
        spine.set_linewidth(1)

    y = 0.97

    # Header
    ax.text(0.05, y, f"[{label}] {item_id}", transform=ax.transAxes,
            fontsize=9, fontproperties=prop_bold, va="top", color="#333333")
    y -= 0.06

    # Metadata
    meta = f"{item.get('dataset')}  |  {item.get('domain')}  |  {item.get('subdomain')}"
    ax.text(0.05, y, meta, transform=ax.transAxes,
            fontsize=8, fontproperties=prop, va="top", color="#666666")
    y -= 0.06

    # Question text
    question = clean_question(item["question"])
    wrapped = textwrap.fill(question, width=45)
    ax.text(0.05, y, wrapped, transform=ax.transAxes,
            fontsize=7.5, fontproperties=prop, va="top", color="#222222",
            linespacing=1.4)

    # Image in lower portion
    if img is not None:
        inset = ax.inset_axes([0.05, 0.02, 0.9, 0.52])
        inset.imshow(img)
        inset.axis("off")


for target in [0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]:
    diff = np.abs(vals - target)
    best = np.argmin(diff)
    i, j = ri[best], ci[best]
    s = vals[best]
    id_a, id_b = str(ids[i]), str(ids[j])
    a, b = data[id_a], data[id_b]
    img_a, img_b = get_first_image(a), get_first_image(b)

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12, 7))
    fig.patch.set_facecolor(BG_COLOR)
    fig.suptitle(f"Cosine Similarity = {s:.4f}", fontsize=15,
                 fontweight="bold", y=0.98, fontproperties=prop_bold)

    draw_item(ax_l, a, id_a, "A", img_a)
    draw_item(ax_r, b, id_b, "B", img_b)

    fig.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03, wspace=0.06)
    fname = OUT / f"pair_sim_{target:.2f}.png"
    fig.savefig(fname, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  {fname.name}  sim={s:.4f}")

print(f"\nSaved 10 visualizations to {OUT}/")
