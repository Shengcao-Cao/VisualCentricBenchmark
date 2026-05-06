"""Image quality effect analysis on the equivalent-image subset (144 items).

Compares three conditions:
  A. Original text + original image    (from T0 judged files)
  B. Original text + reproduced image  (from image_quality judged files)
  C. Edited text  + reproduced image   (from T3_2 judged files, pruned_scoring)

If B > A, cleaner reproduced images help.
If C < B, the question editing (not image quality) drives the remaining gap.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.dirname(os.path.abspath(__file__))

MODELS = [
    ("gpt-5.4",                       "gpt_5_4",                        "GPT-5.4",              "#2e7d32", "o"),
    ("gpt-5.4-mini",                   "gpt_5_4_mini",                  "GPT-5.4 mini",         "#66bb6a", "o"),
    ("gemini-3.1-pro-preview",         "gemini_3_1_pro_preview",        "Gemini 3.1 Pro",       "#1565c0", "s"),
    ("gemini-3.1-flash-lite-preview",  "gemini_3_1_flash_lite_preview", "Gemini 3.1 Flash-Lite","#42a5f5", "s"),
    ("gemma-4-31b-it",                 "gemma_4_31b",                   "Gemma 4 31B",          "#00897b", "D"),
    ("us.anthropic.claude-opus-4-6-v1","claude_opus_4_6",               "Claude Opus 4.6",      "#e65100", "^"),
    ("us.anthropic.claude-sonnet-4-6", "claude_sonnet_4_6",             "Claude Sonnet 4.6",    "#ff9800", "^"),
    ("qwen.qwen3-vl-235b-a22b",       "qwen3_vl_235b_a22b",           "Qwen3-VL-235B-A22B",   "#9c27b0", "P"),
    ("moonshotai.kimi-k2.5",           "kimi_k2_5",                    "Kimi K2.5",            "#78909c", "X"),
    ("qwen/qwen3.5-397b-a17b",        "open_router_qwen3_5_397b_a17b","Qwen3.5-397B-A17B",    "#6a1b9a", "P"),
]

LEGEND_ORDER = [
    "GPT-5.4", "GPT-5.4 mini",
    "Gemini 3.1 Pro", "Gemini 3.1 Flash-Lite",
    "Claude Opus 4.6", "Claude Sonnet 4.6",
    "Qwen3-VL-235B-A22B", "Qwen3.5-397B-A17B",
    "Gemma 4 31B", "Kimi K2.5",
]


def load(path):
    with open(os.path.join(BASE, path)) as f:
        return json.load(f)


def get_t0_correct(slug, model_key, equiv_ids):
    data = load(f"data/filtered_data_with_solution_hard_{slug}_judged.json")
    out = {}
    for item in data:
        if item is None or item["id"] not in equiv_ids:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        if "correct" in judge:
            out[item["id"]] = bool(judge["correct"])
    return out


def get_iq_correct(slug, model_key, equiv_ids):
    path = f"data/image_quality_{slug}_judged.json"
    data = load(path)
    out = {}
    for item in data:
        if item is None or item["id"] not in equiv_ids:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        if "correct" in judge:
            out[item["id"]] = bool(judge["correct"])
    return out


def get_t3_correct(slug, model_key, equiv_ids):
    path = f"data/filtered_data_with_solution_hard_tier3_2_{slug}_judged.json"
    data = load(path)
    out = {}
    for item in data:
        if item is None or item["id"] not in equiv_ids:
            continue
        qs = item.get("tier3_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("pruned_scoring") or {}
        result = scoring.get(model_key) or {}
        if "correct" in result:
            out[item["id"]] = bool(result["correct"])
    return out


def main():
    equiv_data = load("data/image_quality_equiv_subset_corrected.json")
    equiv_ids = set(item["id"] for item in equiv_data)

    rows = []
    for model_key, slug, label, color, marker in MODELS:
        t0 = get_t0_correct(slug, model_key, equiv_ids)
        iq = get_iq_correct(slug, model_key, equiv_ids)
        t3 = get_t3_correct(slug, model_key, equiv_ids)

        shared = equiv_ids & set(t0) & set(iq) & set(t3)
        if not shared:
            print(f"{label}: no shared items, skipping")
            continue

        a = 100 * np.mean([int(t0[pid]) for pid in shared])
        b = 100 * np.mean([int(iq[pid]) for pid in shared])
        c = 100 * np.mean([int(t3[pid]) for pid in shared])

        rows.append((label, color, marker, a, b, c, len(shared)))
        print(f"{label:30s}  A={a:5.1f}  B={b:5.1f}  C={c:5.1f}  "
              f"B-A={b-a:+5.1f}  C-A={c-a:+5.1f}  n={len(shared)}")

    # ── Markdown ──
    lines = []
    def p(s=""):
        lines.append(s)

    p("# Image Quality Effect Analysis")
    p()
    p("## Setup")
    p()
    p("On the 144-item equivalent-image subset (where the reproduced T3 image is semantically")
    p("equivalent to the original), we compare three conditions:")
    p()
    p("- **A. Orig text + orig image** — baseline (from T0 judged results)")
    p("- **B. Orig text + reproduced image** — isolates image quality effect")
    p("- **C. Edited text + reproduced image** — full Tier 3 setting (from T3_2 judged results, pruned_scoring)")
    p()
    p("If B > A, cleaner programmatic renderings help models. If C < B, question editing")
    p("(textual shortcut removal) degrades performance beyond the image swap.")
    p()

    p("## Results")
    p()
    p("| Model | A: Orig+Orig (%) | B: Orig+Repro (%) | C: Edit+Repro (%) | B−A (pp) | C−A (pp) | n |")
    p("|-------|--:|--:|--:|--:|--:|--:|")
    for label, color, marker, a, b, c, n in rows:
        p(f"| {label} | {a:.1f} | {b:.1f} | {c:.1f} | {b-a:+.1f} | {c-a:+.1f} | {n} |")

    avg_a = np.mean([r[3] for r in rows])
    avg_b = np.mean([r[4] for r in rows])
    avg_c = np.mean([r[5] for r in rows])
    p(f"| **Average** | {avg_a:.1f} | {avg_b:.1f} | {avg_c:.1f} | {avg_b-avg_a:+.1f} | {avg_c-avg_a:+.1f} | — |")
    p()

    p("## How to Reproduce")
    p()
    p("```bash")
    p("conda activate dataset")
    p("python results/image_quality/image_quality.py")
    p("```")

    md = "\n".join(lines) + "\n"
    md_path = os.path.join(OUT, "image_quality.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(f"\nSaved to {md_path}")

    # ── Figure: grouped bar chart ──
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
    })

    model_labels = [r[0] for r in rows]
    vals_a = [r[3] for r in rows]
    vals_b = [r[4] for r in rows]
    vals_c = [r[5] for r in rows]

    x = np.arange(len(model_labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 3.5))
    bars_a = ax.bar(x - width, vals_a, width, label="Orig text + orig image",
                    color="#1565c0", edgecolor="white", linewidth=0.5)
    bars_b = ax.bar(x, vals_b, width, label="Orig text + repro image",
                    color="#2e7d32", edgecolor="white", linewidth=0.5)
    bars_c = ax.bar(x + width, vals_c, width, label="Edited text + repro image (Tier 3)",
                    color="#ef6c00", edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=8, rotation=25, ha="right")
    ax.set_ylabel("Accuracy (%)", fontsize=10)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.grid(axis="y", alpha=0.15, linewidth=0.4)
    ax.legend(fontsize=8, loc="upper right", frameon=True, edgecolor="#dddddd",
              fancybox=False)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "image_quality.pdf"), bbox_inches="tight", dpi=200)
    fig.savefig(os.path.join(OUT, "image_quality.png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("Saved figure.")


if __name__ == "__main__":
    main()
