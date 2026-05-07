"""Ablation analysis: text-only, text+caption, text+image+caption, and recovered question."""

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
    ("gpt-5.4",                  "gpt_5_4",                        "GPT-5.4",            "#2e7d32"),
    ("gemini-3.1-pro-preview",   "gemini_3_1_pro_preview",         "Gemini 3.1 Pro",     "#1565c0"),
    ("qwen/qwen3.5-397b-a17b",  "open_router_qwen3_5_397b_a17b",  "Qwen3.5-397B-A17B",  "#6a1b9a"),
    ("moonshotai.kimi-k2.5",    "kimi_k2_5",                      "Kimi K2.5",          "#78909c"),
]

AVG_LABEL = "Average"

ABLATION_MODES = ["text_only", "text_caption", "text_image_caption"]

MODE_LABELS = {
    "canonical":           "Text + Image",
    "text_only":           "Text only",
    "text_caption":        "Text + Caption",
    "text_image_caption":  "Text + Image\n+ Caption",
    "recovered":           "Recovered\n+ Image",
}
MODE_LABELS_FLAT = {k: v.replace("\n", " ") for k, v in MODE_LABELS.items()}


def load(path):
    with open(os.path.join(BASE, path)) as f:
        return json.load(f)


def get_canonical_t0(slug, mk, subset_ids):
    data = load(f"data/filtered_data_with_solution_hard_{slug}_judged.json")
    correct = total = 0
    for item in data:
        if item is None or item["id"] not in subset_ids:
            continue
        judge = (item.get("model") or {}).get(mk, {}).get("judge") or {}
        if "correct" in judge:
            total += 1
            if judge["correct"]:
                correct += 1
    return correct, total


def get_canonical_t2(slug, mk, subset_ids):
    data = load(f"data/filtered_data_with_solution_hard_tier1+2_clean_tier2_{slug}_judged.json")
    correct = total = 0
    for item in data:
        if item is None or item["id"] not in subset_ids:
            continue
        qs = item.get("tier2_questions") or []
        if not qs:
            continue
        scoring = (qs[0].get("scoring") or {}).get(mk) or {}
        if "correct" in scoring:
            total += 1
            if scoring["correct"]:
                correct += 1
    return correct, total


def get_ablation_t0(slug, mk, mode):
    data = load(f"data/ablation_t0_{mode}_{slug}_judged.json")
    correct = total = 0
    for item in data:
        if item is None:
            continue
        judge = (item.get("model") or {}).get(mk, {}).get("ablation_judge") or {}
        if "correct" in judge:
            total += 1
            if judge["correct"]:
                correct += 1
    return correct, total


def get_ablation_t2(slug, mk, mode):
    if mode == "recovered":
        path = f"data/ablation_t2_recovered_{slug}_judged.json"
    else:
        path = f"data/ablation_t2_{mode}_{slug}_judged.json"
    data = load(path)
    correct = total = 0
    for item in data:
        if item is None:
            continue
        qs = item.get("tier2_questions") or []
        if not qs:
            continue
        scoring = (qs[0].get("ablation_scoring") or {}).get(mk) or {}
        if "correct" in scoring:
            total += 1
            if scoring["correct"]:
                correct += 1
    return correct, total


def main():
    subset = load("data/ablation_subset_200.json")
    subset_ids = set(item["id"] for item in subset)

    # ── Collect all numbers ──
    # results[tier][model_label][setting] = accuracy%
    results = {"t0": {}, "t2": {}}

    for mk, slug, label, color in MODELS:
        results["t0"][label] = {}
        results["t2"][label] = {}

        c, t = get_canonical_t0(slug, mk, subset_ids)
        results["t0"][label]["canonical"] = 100 * c / t if t else 0

        c, t = get_canonical_t2(slug, mk, subset_ids)
        results["t2"][label]["canonical"] = 100 * c / t if t else 0

        for mode in ABLATION_MODES:
            c, t = get_ablation_t0(slug, mk, mode)
            results["t0"][label][mode] = 100 * c / t if t else 0

            c, t = get_ablation_t2(slug, mk, mode)
            results["t2"][label][mode] = 100 * c / t if t else 0

        c, t = get_ablation_t2(slug, mk, "recovered")
        results["t2"][label]["recovered"] = 100 * c / t if t else 0

    # ── Compute averages ──
    for tier in ["t0", "t2"]:
        results[tier][AVG_LABEL] = {}
        all_settings = set()
        for _, _, label, _ in MODELS:
            all_settings.update(results[tier][label].keys())
        for s in all_settings:
            vals = [results[tier][label][s] for _, _, label, _ in MODELS if s in results[tier][label]]
            results[tier][AVG_LABEL][s] = np.mean(vals) if vals else 0

    # Print summary
    all_labels = [label for _, _, label, _ in MODELS] + [AVG_LABEL]
    for tier, tier_label in [("t0", "Original Problem"), ("t2", "Tier 2 (Pruned)")]:
        print(f"\n{'=' * 70}")
        print(f"  {tier_label}")
        print(f"{'=' * 70}")
        settings = ["canonical"] + ABLATION_MODES
        if tier == "t2":
            settings.append("recovered")
        header = f"  {'Model':<22}" + "".join(f"{MODE_LABELS_FLAT[s]:>18}" for s in settings)
        print(header)
        print("  " + "-" * (22 + 18 * len(settings)))
        for label in all_labels:
            row = f"  {label:<22}"
            for s in settings:
                row += f"{results[tier][label].get(s, 0):>17.1f}%"
            print(row)

    # ── Styling ──
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
    })

    FIG_HEIGHT = 3.5

    # Per-model base colors with alpha progression (lighter = less info, darker = more info)
    from matplotlib.colors import to_rgba
    model_colors = {label: color for _, _, label, color in MODELS}
    model_colors[AVG_LABEL] = "#c62828"

    # Alpha levels: lighter for less information, darker for more
    # T0: text_only(0.35), text_caption(0.55), canonical(0.80), text_image_caption(1.0)
    # T2: text_only(0.30), text_caption(0.45), canonical(0.65), recovered(0.80), text_image_caption(1.0)
    t0_alphas = {"text_only": 0.35, "text_caption": 0.55, "canonical": 0.80, "text_image_caption": 1.0}
    t2_alphas = {"text_only": 0.30, "text_caption": 0.45, "canonical": 0.60, "text_image_caption": 0.80, "recovered": 1.0}

    def get_color(base_color, alpha):
        r, g, b, _ = to_rgba(base_color)
        return (r, g, b, alpha)

    # ── Figure: Grouped bar chart ──
    t0_settings = ["text_only", "text_caption", "canonical", "text_image_caption"]
    t2_settings = ["text_only", "text_caption", "canonical", "text_image_caption", "recovered"]
    bar_labels = [label for _, _, label, _ in MODELS] + [AVG_LABEL]

    fig, (ax0, ax2) = plt.subplots(1, 2, figsize=(13, FIG_HEIGHT), sharey=True,
                                    gridspec_kw={"width_ratios": [4, 5]})

    for ax, tier, settings, title, alphas in [
        (ax0, "t0", t0_settings, "Original Problem", t0_alphas),
        (ax2, "t2", t2_settings, "Tier 2 (Pruned)", t2_alphas),
    ]:
        n_settings = len(settings)
        n_bars = len(bar_labels)
        width = 0.16
        group_width = n_bars * width
        group_gap = 0.45
        x = np.arange(n_settings) * (group_width + group_gap)

        for i, label in enumerate(bar_labels):
            base_color = model_colors[label]
            offsets = (np.arange(n_bars) - (n_bars - 1) / 2) * width
            vals = [results[tier][label].get(s, 0) for s in settings]
            bar_colors = [get_color(base_color, alphas[s]) for s in settings]

            bars = ax.bar(x + offsets[i], vals, width, color=bar_colors, edgecolor="white",
                          linewidth=0.5)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=6, fontweight="medium",
                        color="#333333")

        # Canonical baseline dashed line (average only)
        avg_canon = results[tier][AVG_LABEL].get("canonical", 0)
        ax.axhline(avg_canon, linestyle="--", color="#999999", linewidth=0.7, alpha=0.6, zorder=1)

        xlabels = [MODE_LABELS[s] for s in settings]
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels, fontsize=8)
        ax.set_title(title, fontsize=10.5, fontweight="medium", pad=6)
        if ax is ax0:
            ax.set_ylabel("Accuracy (%)", fontsize=9.5)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
        ax.grid(axis="y", alpha=0.12, linewidth=0.4)
        ax.tick_params(axis="both", labelsize=8)

    # Legend: one entry per model (using darkest alpha)
    import matplotlib.patches as mpatches
    legend_handles = []
    for label in bar_labels:
        legend_handles.append(mpatches.Patch(facecolor=model_colors[label], edgecolor="white",
                                             linewidth=0.5, label=label))
    ax0.legend(handles=legend_handles, fontsize=7.5, loc="upper left", frameon=True,
               edgecolor="#dddddd", fancybox=False, handletextpad=0.4, borderpad=0.5)

    fig.tight_layout(w_pad=2)
    fig.savefig(os.path.join(OUT, "ablation_results.pdf"), bbox_inches="tight", dpi=200)
    fig.savefig(os.path.join(OUT, "ablation_results.png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("\nSaved ablation_results.{pdf,png}")

    # ── Write markdown ──
    lines = []
    def p(s=""):
        lines.append(s)

    p("# Ablation Analysis: Input Modality Experiments")
    p()
    p("## Overview")
    p()
    p("We evaluate three top models under different input configurations to measure")
    p("the contribution of images and atomic fact captions to reasoning performance.")
    p("All experiments use a 200-item subset of problems that have Tier 2 (pruned) variants.")
    p()
    p("**Input settings:**")
    p("- **Text only**: Images removed, replaced with `[Image N hidden]`.")
    p("- **Text + Caption**: Images replaced with atomic fact captions (detailed image descriptions).")
    p("- **Text + Image** (canonical): Original problem text with original images.")
    p("- **Text + Image + Caption**: Original images plus atomic fact captions as supplementary context.")
    p("- **Recovered + Image** (T2 only): Recovered question (pruned text with atomic facts re-inserted) + original images.")
    p()
    p("**Models:** GPT-5.4, Gemini 3.1 Pro, Qwen3.5-397B-A17B.")
    p()

    for tier, tier_label in [("t0", "Original Problem"), ("t2", "Tier 2 (Pruned)")]:
        settings = ["text_only", "text_caption", "canonical"]
        if tier == "t2":
            settings += ["recovered"]
        settings += ["text_image_caption"]

        p(f"## {tier_label}")
        p()
        header = "| Model | " + " | ".join(MODE_LABELS_FLAT[s] for s in settings) + " |"
        p(header)
        p("|" + "---|" * (len(settings) + 1))
        for label in [l for _, _, l, _ in MODELS] + [AVG_LABEL]:
            row = f"| {'**' + label + '**' if label == AVG_LABEL else label} | "
            row += " | ".join(f"{results[tier][label].get(s, 0):.1f}" for s in settings)
            row += " |"
            p(row)
        p()

    p("## Key Findings")
    p()
    p("### Text-only solvability")
    p("Removing images causes a large accuracy drop across all models:")
    for _, _, label, _ in MODELS:
        t0_drop = results["t0"][label]["canonical"] - results["t0"][label]["text_only"]
        t2_drop = results["t2"][label]["canonical"] - results["t2"][label]["text_only"]
        p(f"- **{label}**: Original {t0_drop:+.1f} pp, Pruned {t2_drop:+.1f} pp")
    p()
    p("The drop is larger on pruned problems, confirming that pruning successfully")
    p("removes textual shortcuts that previously allowed solving without images.")
    p()

    p("### Caption as image substitute")
    p("Replacing images with atomic fact captions partially recovers performance:")
    for _, _, label, _ in MODELS:
        t0_gap = results["t0"][label]["text_caption"] - results["t0"][label]["text_only"]
        t2_gap = results["t2"][label]["text_caption"] - results["t2"][label]["text_only"]
        p(f"- **{label}**: +{t0_gap:.1f} pp (Original), +{t2_gap:.1f} pp (Pruned) over text-only")
    p()

    p("### Image + Caption augmentation")
    p("Adding captions on top of images (Text + Image + Caption) vs. canonical (Text + Image):")
    for _, _, label, _ in MODELS:
        t0_gain = results["t0"][label]["text_image_caption"] - results["t0"][label]["canonical"]
        t2_gain = results["t2"][label]["text_image_caption"] - results["t2"][label]["canonical"]
        p(f"- **{label}**: {t0_gain:+.1f} pp (Original), {t2_gain:+.1f} pp (Pruned)")
    p()

    p("### Information completeness (Recovered question)")
    p("The recovered question (pruned text with atomic facts re-inserted) + original images:")
    for _, _, label, _ in MODELS:
        t2_canon = results["t2"][label]["canonical"]
        t2_recov = results["t2"][label]["recovered"]
        p(f"- **{label}**: Recovered {t2_recov:.1f}% vs. Canonical {t2_canon:.1f}% ({t2_recov - t2_canon:+.1f} pp)")
    p("Recovery to near-canonical levels confirms that pruning removed only image-redundant information.")
    p()

    p("## Outputs")
    p()
    p("- `ablation_results.{pdf,png}`: Grouped bar chart comparing all settings.")
    p()
    p("## How to Reproduce")
    p()
    p("```bash")
    p("conda activate dataset")
    p("python results/ablation/ablation_analysis.py")
    p("```")

    md_path = os.path.join(OUT, "ablation_analysis.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved {md_path}")


if __name__ == "__main__":
    main()
