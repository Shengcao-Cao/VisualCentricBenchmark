"""Pruning ratio analysis: accuracy drop vs. fraction of characters removed in Tier 2."""

import json
import os
import numpy as np
from scipy import stats
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


def get_t0_correct(slug, model_key):
    data = load(f"data/filtered_data_with_solution_hard_{slug}_judged.json")
    out = {}
    for item in data:
        if item is None:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        if "correct" in judge:
            out[item["id"]] = bool(judge["correct"])
    return out


def get_t2_correct(slug, model_key):
    data = load(f"data/filtered_data_with_solution_hard_tier1+2_clean_tier2_{slug}_judged.json")
    out = {}
    for item in data:
        if item is None:
            continue
        t2qs = item.get("tier2_questions") or []
        if not t2qs:
            continue
        scoring = t2qs[0].get("scoring") or {}
        result = scoring.get(model_key) or {}
        if "correct" in result:
            out[item["id"]] = bool(result["correct"])
    return out


def corr(x, y):
    x, y = np.array(x, dtype=float), np.array(y, dtype=float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return {"pearson_r": float("nan"), "pearson_p": float("nan"),
                "spearman_r": float("nan"), "spearman_p": float("nan"), "n": len(x)}
    pr, pp = stats.pearsonr(x, y)
    sr, sp = stats.spearmanr(x, y)
    return {"pearson_r": pr, "pearson_p": pp, "spearman_r": sr, "spearman_p": sp, "n": int(len(x))}


def main():
    clean = load("data/filtered_data_with_solution_hard_tier1+2_clean.json")

    # Compute per-problem pruning ratio (char-based), exclude negatives
    pruning_ratios = {}
    for item in clean:
        if not item.get("tier2_questions"):
            continue
        orig_len = len(item["question"])
        pruned_len = len(item["tier2_questions"][0]["pruned_question"])
        if orig_len == 0:
            continue
        ratio = 1 - pruned_len / orig_len
        if ratio < 0:
            continue
        pruning_ratios[item["id"]] = ratio

    ratios_arr = np.array(list(pruning_ratios.values()))
    print(f"Items with valid pruning ratio: {len(pruning_ratios)}")
    print(f"Excluded (negative ratio, i.e. text expanded): {sum(1 for item in clean if item.get('tier2_questions') and len(item['question']) > 0 and 1 - len(item['tier2_questions'][0]['pruned_question']) / len(item['question']) < 0)}")
    print(f"Ratio stats: mean={ratios_arr.mean():.3f}, median={np.median(ratios_arr):.3f}, "
          f"Q1={np.percentile(ratios_arr, 25):.3f}, Q3={np.percentile(ratios_arr, 75):.3f}")

    # Fixed thresholds
    t1_bound, t2_bound = 0.15, 0.30
    print(f"Bin boundaries: {t1_bound}, {t2_bound}")

    BINS = [
        (0.0, t1_bound,     "[0, 15%]"),
        (t1_bound, t2_bound, "(15%, 30%]"),
        (t2_bound, 1.001,    "(30%, 1]"),
    ]

    # Collect per-(problem, model) data
    all_rows = []
    model_agg = {}

    for model_key, slug, label, color, marker in MODELS:
        t0 = get_t0_correct(slug, model_key)
        t2 = get_t2_correct(slug, model_key)

        for pid, ratio in pruning_ratios.items():
            if pid in t0 and pid in t2:
                all_rows.append({
                    "slug": slug, "label": label, "pid": pid,
                    "ratio": ratio, "t0": int(t0[pid]), "t2": int(t2[pid]),
                    "delta": int(t2[pid]) - int(t0[pid]),
                })

        # Per-model stats
        pairs = [(pruning_ratios[pid], int(t0[pid]), int(t2[pid]))
                 for pid in pruning_ratios if pid in t0 and pid in t2]
        if pairs:
            rs = [r for r, _, _ in pairs]
            deltas = [t2c - t0c for _, t0c, t2c in pairs]
            c = corr(rs, deltas)
            t0_acc = 100 * np.mean([t0c for _, t0c, _ in pairs])
            t2_acc = 100 * np.mean([t2c for _, _, t2c in pairs])
            model_agg[label] = {
                "t0_acc": t0_acc, "t2_acc": t2_acc,
                "delta": t2_acc - t0_acc, "corr": c,
                "color": color, "marker": marker,
            }
            print(f"\n{label}")
            print(f"  T0={t0_acc:.1f}%  T2={t2_acc:.1f}%  Δ={t2_acc - t0_acc:+.1f}pp")
            print(f"  corr(ratio, Δ): r={c['pearson_r']:.3f} (p={c['pearson_p']:.1e})  "
                  f"ρ={c['spearman_r']:.3f} (p={c['spearman_p']:.1e})  n={c['n']}")

            # Per-bin accuracy
            for lo, hi, blabel in BINS:
                bin_t0 = [t0c for r, t0c, t2c in pairs if lo <= r < hi]
                bin_t2 = [t2c for r, t0c, t2c in pairs if lo <= r < hi]
                if bin_t0:
                    bt0 = 100 * np.mean(bin_t0)
                    bt2 = 100 * np.mean(bin_t2)
                    print(f"    {blabel.split(chr(10))[0]:>6}: T0={bt0:.1f}%  T2={bt2:.1f}%  Δ={bt2 - bt0:+.1f}pp  n={len(bin_t0)}")

    # ── Styling ──
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
    })

    FIG_HEIGHT = 3.6
    group_colors = ["#ef6c00", "#558b2f", "#1565c0"]

    # ── Figure: Grouped bar chart with Δ annotation ──
    bin_t0_accs, bin_t2_accs, bin_ns = [], [], []
    for lo, hi, _ in BINS:
        t0_vals = [row["t0"] for row in all_rows if lo <= row["ratio"] < hi]
        t2_vals = [row["t2"] for row in all_rows if lo <= row["ratio"] < hi]
        bin_t0_accs.append(100 * np.mean(t0_vals) if t0_vals else 0)
        bin_t2_accs.append(100 * np.mean(t2_vals) if t2_vals else 0)
        bin_ns.append(len(t0_vals))

    deltas = [t2 - t0 for t0, t2 in zip(bin_t0_accs, bin_t2_accs)]

    fig, ax = plt.subplots(figsize=(4.5, FIG_HEIGHT))
    x = np.arange(len(BINS))
    w = 0.3

    for i in range(len(BINS)):
        light = matplotlib.colors.to_rgba(group_colors[i], alpha=0.35)
        ax.bar(x[i] - w / 2, bin_t0_accs[i], w, color=light, edgecolor="white", linewidth=0.8,
               label="Original Problem" if i == 0 else None)
        ax.bar(x[i] + w / 2, bin_t2_accs[i], w, color=group_colors[i], edgecolor="white", linewidth=0.8,
               label="Tier 2 (Pruned)" if i == 0 else None)

    for i in range(len(BINS)):
        top = max(bin_t0_accs[i], bin_t2_accs[i])
        ax.annotate(f"{deltas[i]:+.1f}", xy=(x[i], top + 1.5),
                    ha="center", va="bottom", fontsize=10, fontweight="medium",
                    color=group_colors[i])

    xlabels = [b[2] for b in BINS]
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=11)
    ax.set_ylabel("Accuracy (%)", fontsize=12)
    ax.set_xlabel("Pruning Ratio", fontsize=12)
    ax.set_ylim(0, 78)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.grid(axis="y", alpha=0.15, linewidth=0.4)
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(fontsize=10, loc="lower left", framealpha=0.9, edgecolor="#dddddd")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "pruning_ratio.pdf"), bbox_inches="tight", dpi=200)
    fig.savefig(os.path.join(OUT, "pruning_ratio.png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("\nSaved pruning ratio figure.")

    # ── Write markdown ──
    lines = []

    def p(s=""):
        lines.append(s)

    p("# Pruning Ratio Analysis")
    p()
    p("## Overview")
    p()
    p("We stratify Tier 2 problems by the fraction of characters removed during pruning and examine "
      "whether heavier pruning causes larger accuracy drops. A positive correlation between pruning "
      "ratio and accuracy degradation confirms that the pruning signal is meaningful and proportional.")
    p()
    p("**Pruning ratio** = 1 − len(pruned_question) / len(original_question), measured in characters.")
    p()
    p(f"Items with valid pruning ratio (non-negative): **{len(pruning_ratios)}** out of 1,035 T2 items. "
      f"{1035 - len(pruning_ratios)} items excluded because the pruned question is longer than the original "
      f"(these are problems where the original text is minimal, e.g. `<image_1>`, and the pruning pipeline "
      f"expanded it into explicit text).")
    p()
    p(f"Pruning ratio: mean = {ratios_arr.mean():.1%}, median = {np.median(ratios_arr):.1%}, "
      f"Q1 = {np.percentile(ratios_arr, 25):.1%}, Q3 = {np.percentile(ratios_arr, 75):.1%}.")
    p()
    p(f"Tercile boundaries: {t1_bound:.1%} and {t2_bound:.1%}.")
    p()

    p("## Outputs")
    p()
    p("### `pruning_ratio.{pdf,png}`")
    p()
    p("Two-panel figure. Left: original and pruned (T2) accuracy by pruning ratio tercile, pooled "
      "across all 10 models. Right: accuracy change (Δ = T2 − Original) by tercile.")
    p()

    # Summary table
    p("## Pooled Results (across models)")
    p()
    p("| Pruning Ratio | n | Original (%) | Pruned (%) | Δ (pp) |")
    p("|--------------|---:|------------:|----------:|-------:|")
    for i, (lo, hi, blabel) in enumerate(BINS):
        label_short = blabel.split("\n")[0]
        p(f"| {label_short} | {bin_ns[i]:,} | {bin_t0_accs[i]:.1f} | {bin_t2_accs[i]:.1f} | {deltas[i]:+.1f} |")
    p()

    # Per-model correlation table
    p("## Per-Model Correlation: Pruning Ratio vs. Accuracy Change")
    p()
    p("| Model | Original (%) | Pruned (%) | Δ (pp) | Pearson r | p-value | Spearman ρ | p-value |")
    p("|-------|------------:|----------:|-------:|----------:|--------:|-----------:|--------:|")
    for _, _, label, _, _ in MODELS:
        if label in model_agg:
            m = model_agg[label]
            c = m["corr"]
            p(f"| {label} | {m['t0_acc']:.1f} | {m['t2_acc']:.1f} | {m['delta']:+.1f} | "
              f"{c['pearson_r']:.3f} | {c['pearson_p']:.1e} | {c['spearman_r']:.3f} | {c['spearman_p']:.1e} |")
    p()

    # Overall correlation (pooled)
    all_ratios = [row["ratio"] for row in all_rows]
    all_deltas = [row["delta"] for row in all_rows]
    c_all = corr(all_ratios, all_deltas)
    p(f"**Pooled correlation** (n={c_all['n']:,}): "
      f"r = {c_all['pearson_r']:.3f} (p = {c_all['pearson_p']:.1e}), "
      f"ρ = {c_all['spearman_r']:.3f} (p = {c_all['spearman_p']:.1e})")
    p()

    p("## How to Reproduce")
    p()
    p("```bash")
    p("conda activate dataset")
    p("python results/pruning_ratio/pruning_ratio.py")
    p("```")

    md = "\n".join(lines) + "\n"
    md_path = os.path.join(OUT, "pruning_ratio.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(f"Saved markdown to {md_path}")


if __name__ == "__main__":
    main()
