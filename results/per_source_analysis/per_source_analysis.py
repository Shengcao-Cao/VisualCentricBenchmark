"""Per-source-dataset analysis: T0 vs T3_2 accuracy and delta, grouped by source benchmark."""

import json
import os
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.dirname(os.path.abspath(__file__))

MODELS = [
    ("gpt-5.4",                       "gpt_5_4",                        "GPT-5.4"),
    ("gpt-5.4-mini",                   "gpt_5_4_mini",                  "GPT-5.4 mini"),
    ("gemini-3.1-pro-preview",         "gemini_3_1_pro_preview",        "Gemini 3.1 Pro"),
    ("gemini-3.1-flash-lite-preview",  "gemini_3_1_flash_lite_preview", "Gemini 3.1 Flash-Lite"),
    ("gemma-4-31b-it",                 "gemma_4_31b",                   "Gemma 4 31B"),
    ("us.anthropic.claude-opus-4-6-v1","claude_opus_4_6",               "Claude Opus 4.6"),
    ("us.anthropic.claude-sonnet-4-6", "claude_sonnet_4_6",             "Claude Sonnet 4.6"),
    ("qwen.qwen3-vl-235b-a22b",       "qwen3_vl_235b_a22b",           "Qwen3-VL-235B-A22B"),
    ("moonshotai.kimi-k2.5",           "kimi_k2_5",                    "Kimi K2.5"),
    ("qwen/qwen3.5-397b-a17b",        "open_router_qwen3_5_397b_a17b","Qwen3.5-397B-A17B"),
]

SOURCE_ORDER = [
    "Geometry3k",
    "MathVerse",
    "MathVision",
    "MathVista",
    "OlympiadBench",
    "OlympicArena",
    "MMMU",
    "EMMA",
    "MME_Reasoning",
    "HumanityLastExam",
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


def get_t32_correct(slug, model_key):
    data = load(f"data/filtered_data_with_solution_hard_tier3_2_{slug}_judged.json")
    out = {}
    for item in data:
        if item is None:
            continue
        t3qs = item.get("tier3_questions") or []
        if not t3qs:
            continue
        scoring = t3qs[0].get("pruned_scoring") or {}
        result = scoring.get(model_key) or {}
        if "correct" in result:
            out[item["id"]] = bool(result["correct"])
    return out


def main():
    t32_data = load("data/filtered_data_with_solution_hard_tier3_2.json")
    id_to_source = {item["id"]: item["dataset"] for item in t32_data}
    t32_ids = set(id_to_source.keys())

    sources_present = sorted(set(id_to_source.values()),
                             key=lambda s: SOURCE_ORDER.index(s) if s in SOURCE_ORDER else 999)
    source_counts = {}
    for src in sources_present:
        source_counts[src] = sum(1 for v in id_to_source.values() if v == src)

    # Collect per-(model, source) T0 and T3_2 accuracy
    # rows[model_label][source] = (t0_acc, t32_acc, delta)
    rows = {}
    for model_key, slug, label in MODELS:
        t0 = get_t0_correct(slug, model_key)
        t32 = get_t32_correct(slug, model_key)
        rows[label] = {}
        for src in sources_present:
            ids = [pid for pid, s in id_to_source.items() if s == src]
            t0_vals = [int(t0[pid]) for pid in ids if pid in t0]
            t32_vals = [int(t32[pid]) for pid in ids if pid in t32]
            if t0_vals and t32_vals:
                t0_acc = 100 * np.mean(t0_vals)
                t32_acc = 100 * np.mean(t32_vals)
                rows[label][src] = (t0_acc, t32_acc, t32_acc - t0_acc)

    # Also compute average across models per source
    avg_row = {}
    for src in sources_present:
        t0_accs = [rows[label][src][0] for _, _, label in MODELS if src in rows[label]]
        t32_accs = [rows[label][src][1] for _, _, label in MODELS if src in rows[label]]
        if t0_accs:
            avg_row[src] = (np.mean(t0_accs), np.mean(t32_accs), np.mean(t32_accs) - np.mean(t0_accs))

    # ── Write markdown ──
    lines = []

    def p(s=""):
        lines.append(s)

    p("# Per-Source-Dataset Analysis: Original vs. Tier 3 Accuracy")
    p()
    p("## Overview")
    p()
    p(f"We report accuracy on the original problem (Orig) and Tier 3 (T3) for each of the "
      f"{len(sources_present)} source datasets represented in the 283-item Tier 3 subset, "
      f"along with the accuracy change (Δ = T3 − Orig).")
    p()
    p("If problems from older, widely-distributed benchmarks (e.g., Geometry3k, OlympiadBench) "
      "show larger drops than recent benchmarks (e.g., HumanityLastExam), this provides "
      "circumstantial evidence that data contamination drives part of the generalization gap.")
    p()

    p("## Source Dataset Sizes (within Tier 3 subset)")
    p()
    p("| Source | Count |")
    p("|--------|------:|")
    for src in sources_present:
        p(f"| {src} | {source_counts[src]} |")
    p()

    # ── Per-model table ──
    p("## Per-Model Breakdown")
    p()

    for _, _, label in MODELS:
        p(f"### {label}")
        p()
        p("| Source | Orig (%) | T3 (%) | Δ (pp) |")
        p("|--------|--------:|------:|-------:|")
        for src in sources_present:
            if src in rows[label]:
                t0_a, t32_a, delta = rows[label][src]
                p(f"| {src} | {t0_a:.1f} | {t32_a:.1f} | {delta:+.1f} |")
            else:
                p(f"| {src} | — | — | — |")
        p()

    # ── Summary table: average across models ──
    p("## Average Across Models")
    p()
    p("| Source | Count | Orig (%) | T3 (%) | Δ (pp) |")
    p("|--------|------:|--------:|------:|-------:|")
    for src in sources_present:
        if src in avg_row:
            t0_a, t32_a, delta = avg_row[src]
            p(f"| {src} | {source_counts[src]} | {t0_a:.1f} | {t32_a:.1f} | {delta:+.1f} |")
    p()

    # ── Compact cross-table: sources as columns, models as rows ──
    p("## Compact Table: Δ (T3 − Orig) by Model and Source")
    p()
    header = "| Model | " + " | ".join(f"{s} ({source_counts[s]})" for s in sources_present) + " | All |"
    p(header)
    p("|" + "---|" * (len(sources_present) + 2))
    for _, _, label in MODELS:
        vals = []
        all_deltas = []
        for src in sources_present:
            if src in rows[label]:
                delta = rows[label][src][2]
                vals.append(f"{delta:+.1f}")
                all_deltas.append(delta)
            else:
                vals.append("—")
        overall = f"{np.mean(all_deltas):+.1f}" if all_deltas else "—"
        p(f"| {label} | " + " | ".join(vals) + f" | {overall} |")

    # Average row
    avg_vals = []
    all_avg_deltas = []
    for src in sources_present:
        if src in avg_row:
            avg_vals.append(f"{avg_row[src][2]:+.1f}")
            all_avg_deltas.append(avg_row[src][2])
        else:
            avg_vals.append("—")
    overall_avg = f"{np.mean(all_avg_deltas):+.1f}" if all_avg_deltas else "—"
    p(f"| **Average** | " + " | ".join(avg_vals) + f" | {overall_avg} |")
    p()

    p("## How to Reproduce")
    p()
    p("```bash")
    p("conda activate dataset")
    p("python results/per_source_analysis/per_source_analysis.py")
    p("```")

    md = "\n".join(lines) + "\n"
    md_path = os.path.join(OUT, "per_source_analysis.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(md)
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
