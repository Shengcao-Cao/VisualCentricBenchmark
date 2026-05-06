"""Analyze correlation between Tier-1 perception accuracy and original/T2 reasoning correctness."""

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

# (model_key, file_slug, display_name, color, marker, family)
MODELS = [
    ("gpt-5.4",                       "gpt_5_4",                        "GPT-5.4",                "#2e7d32", "o",  "GPT"),
    ("gpt-5.4-mini",                   "gpt_5_4_mini",                  "GPT-5.4 mini",           "#66bb6a", "o",  "GPT"),
    ("gemini-3.1-pro-preview",         "gemini_3_1_pro_preview",        "Gemini 3.1 Pro",         "#1565c0", "s",  "Gemini"),
    ("gemini-3.1-flash-lite-preview",  "gemini_3_1_flash_lite_preview", "Gemini 3.1 Flash-Lite",  "#42a5f5", "s",  "Gemini"),
    ("gemma-4-31b-it",                 "gemma_4_31b",                   "Gemma 4 31B",            "#00897b", "D",  "Gemma"),
    ("us.anthropic.claude-opus-4-6-v1","claude_opus_4_6",               "Claude Opus 4.6",        "#e65100", "^",  "Claude"),
    ("us.anthropic.claude-sonnet-4-6", "claude_sonnet_4_6",             "Claude Sonnet 4.6",      "#ff9800", "^",  "Claude"),
    ("qwen.qwen3-vl-235b-a22b",       "qwen3_vl_235b_a22b",           "Qwen3-VL-235B-A22B",     "#9c27b0", "P",  "Qwen"),
    ("moonshotai.kimi-k2.5",           "kimi_k2_5",                    "Kimi K2.5",              "#78909c", "X",  "Kimi"),
    ("qwen/qwen3.5-397b-a17b",        "open_router_qwen3_5_397b_a17b","Qwen3.5-397B-A17B",      "#6a1b9a", "P",  "Qwen"),
]

LEGEND_ORDER = [
    "GPT-5.4", "GPT-5.4 mini",
    "Gemini 3.1 Pro", "Gemini 3.1 Flash-Lite",
    "Claude Opus 4.6", "Claude Sonnet 4.6",
    "Qwen3-VL-235B-A22B", "Qwen3.5-397B-A17B",
    "Gemma 4 31B", "Kimi K2.5",
]

T1_BINS = [
    (-0.001, 1/3 + 0.001, "[0, 1/3]"),
    (1/3 + 0.001, 2/3 + 0.001, "(1/3, 2/3]"),
    (2/3 + 0.001, 1.001,       "(2/3, 1]"),
]


def load(path):
    with open(os.path.join(BASE, path)) as f:
        return json.load(f)


def get_t1_scores(slug, model_key):
    data = load(f"data/filtered_data_with_solution_hard_tier1+2_clean_tier1_{slug}.json")
    scores = {}
    for item in data:
        qs = item["tier1_questions"]
        if not qs:
            continue
        correct = sum(1 for q in qs if q.get("predictions", {}).get(model_key) == q.get("gt_answer"))
        scores[item["id"]] = correct / len(qs)
    return scores


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
    # ── Collect per-(problem, model) data ──
    all_rows = []
    model_agg = []

    for model_key, slug, label, color, marker, family in MODELS:
        t1 = get_t1_scores(slug, model_key)
        t0 = get_t0_correct(slug, model_key)
        t2 = get_t2_correct(slug, model_key)

        t1_vals = []
        t0_pairs, t2_pairs = [], []

        for pid in t1:
            row = {"t1": t1[pid]}
            if pid in t0:
                row["t0"] = int(t0[pid])
            if pid in t2:
                row["t2"] = int(t2[pid])
            all_rows.append((slug, pid, row))

            t1_vals.append(t1[pid])
            if pid in t0:
                t0_pairs.append((t1[pid], int(t0[pid])))
            if pid in t2:
                t2_pairs.append((t1[pid], int(t2[pid])))

        mean_t1 = np.mean(t1_vals)
        mean_t0 = np.mean([v for _, v in t0_pairs]) if t0_pairs else float("nan")
        mean_t2 = np.mean([v for _, v in t2_pairs]) if t2_pairs else float("nan")
        model_agg.append((label, color, marker, mean_t1, mean_t0, mean_t2))

        c0 = corr([x for x, _ in t0_pairs], [y for _, y in t0_pairs]) if t0_pairs else None
        c2 = corr([x for x, _ in t2_pairs], [y for _, y in t2_pairs]) if t2_pairs else None

        print(f"\n{'─'*60}")
        print(f"{label}")
        print(f"  T1 mean: {mean_t1:.3f}  Original acc: {mean_t0:.3f}  T2 acc: {mean_t2:.3f}")
        for name, c in [("Original", c0), ("T2", c2)]:
            if c:
                print(f"  T1→{name}  r={c['pearson_r']:.3f} (p={c['pearson_p']:.1e})  "
                      f"ρ={c['spearman_r']:.3f} (p={c['spearman_p']:.1e})  n={c['n']}")

    # ── Model-level correlation ──
    labels = [m[0] for m in model_agg]
    agg_t1 = [m[3] for m in model_agg]
    agg_t0 = [m[4] for m in model_agg]
    agg_t2 = [m[5] for m in model_agg]

    print(f"\n{'═'*60}")
    print(f"Model-level correlations (n={len(MODELS)})")
    for name, vals in [("Original", agg_t0), ("T2", agg_t2)]:
        c = corr(agg_t1, vals)
        print(f"  T1→{name}  r={c['pearson_r']:.3f} (p={c['pearson_p']:.3f})  "
              f"ρ={c['spearman_r']:.3f} (p={c['spearman_p']:.3f})")

    # ── Styling ──
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
    })
    bar_colors = ["#ef6c00", "#558b2f", "#1565c0"]

    FIG_HEIGHT = 3.6

    # ── Figure 1: Binned bar chart (pooled across models) ──
    fig, axes = plt.subplots(1, 2, figsize=(7, FIG_HEIGHT), sharey=True)
    tier_names = ["Original Problem", "Tier 2 (Pruned)"]
    tier_keys = ["t0", "t2"]

    for ax, tname, tkey in zip(axes, tier_names, tier_keys):
        bin_accs = []
        bin_ns = []
        for lo, hi, _ in T1_BINS:
            vals = [row[tkey] for _, _, row in all_rows if tkey in row and lo <= row["t1"] < hi]
            bin_accs.append(100 * np.mean(vals) if vals else 0)
            bin_ns.append(len(vals))

        x = np.arange(len(T1_BINS))
        bars = ax.bar(x, bin_accs, width=0.55, color=bar_colors, edgecolor="white", linewidth=0.8)
        for bar, acc in zip(bars, bin_accs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                    f"{acc:.1f}", ha="center", va="bottom", fontsize=10, fontweight="medium")

        xlabels = [b[2] for b in T1_BINS]
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels, fontsize=11)
        ax.set_title(tname, fontsize=12, fontweight="medium", pad=6)
        ax.set_ylim(0, 72)
        ax.set_xlabel("Tier 1 Accuracy", fontsize=12)
        if ax is axes[0]:
            ax.set_ylabel("Accuracy (%)", fontsize=12)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
        ax.grid(axis="y", alpha=0.15, linewidth=0.4)
        ax.tick_params(axis="both", labelsize=10)

    fig.tight_layout(w_pad=1.5)
    fig.savefig(os.path.join(OUT, "t1_correlation_binned.pdf"), bbox_inches="tight", dpi=200)
    fig.savefig(os.path.join(OUT, "t1_correlation_binned.png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("\nSaved binned bar chart.")

    # ── Figure 2: Model-level scatter with marker+color legend ──
    fig2, axes2 = plt.subplots(1, 2, figsize=(9.5, FIG_HEIGHT), sharey=False,
                                gridspec_kw={"right": 0.74})

    for ax, tname, vals in zip(axes2, tier_names, [agg_t0, agg_t2]):
        xvals = [100 * v for v in agg_t1]
        yvals = [100 * v for v in vals]

        for i, (lbl, color, marker, *_) in enumerate(model_agg):
            ax.scatter(xvals[i], yvals[i], s=75, c=color, marker=marker,
                       zorder=3, edgecolors="white", linewidth=0.7)

        c = corr(agg_t1, vals)
        xf, yf = np.array(xvals), np.array(yvals)
        z = np.polyfit(xf, yf, 1)
        xline = np.linspace(min(xf) - 1.5, max(xf) + 1.5, 100)
        ax.plot(xline, np.polyval(z, xline), "--", color="#bdbdbd", linewidth=1, zorder=1)

        ax.set_title(f"{tname}  (r = {c['pearson_r']:.2f}, ρ = {c['spearman_r']:.2f})",
                     fontsize=12, fontweight="medium", pad=6)
        ax.set_xlabel("Mean Tier 1 Accuracy (%)", fontsize=12)
        if ax is axes2[0]:
            ax.set_ylabel("Accuracy (%)", fontsize=12)
        ax.grid(True, alpha=0.12, linewidth=0.4)
        ax.tick_params(axis="both", labelsize=10)

    agg_by_name = {lbl: (color, marker) for lbl, color, marker, *_ in model_agg}
    legend_handles = []
    for name in LEGEND_ORDER:
        color, marker = agg_by_name[name]
        h = matplotlib.lines.Line2D([], [], color=color, marker=marker, linestyle="None",
                                     markersize=8, markeredgecolor="white", markeredgewidth=0.7,
                                     label=name)
        legend_handles.append(h)

    fig2.legend(handles=legend_handles, loc="center right",
                bbox_to_anchor=(0.99, 0.5), fontsize=9, frameon=True,
                edgecolor="#dddddd", fancybox=False, handletextpad=0.4,
                borderpad=0.6, labelspacing=0.5)

    fig2.tight_layout(rect=[0, 0, 0.74, 1])
    fig2.savefig(os.path.join(OUT, "t1_correlation_scatter.pdf"), bbox_inches="tight", dpi=200)
    fig2.savefig(os.path.join(OUT, "t1_correlation_scatter.png"), bbox_inches="tight", dpi=200)
    plt.close(fig2)
    print("Saved model-level scatter.")


if __name__ == "__main__":
    main()
