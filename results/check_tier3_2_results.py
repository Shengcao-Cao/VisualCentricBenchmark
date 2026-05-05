"""Check tier3_2 (edited+pruned) evaluation results: accuracy and comparison with tier0 and tier3."""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

PREFIX_T32 = "filtered_data_with_solution_hard_tier3_2_"
PREFIX_T3 = "filtered_data_with_solution_hard_tier3_jpg_"
PREFIX_T0 = "filtered_data_with_solution_hard_"

MODELS = [
    ("gpt-5.4",                          "gpt_5_4"),
    ("gpt-5.4-mini",                     "gpt_5_4_mini"),
    ("gemini-3.1-pro-preview",           "gemini_3_1_pro_preview"),
    ("gemini-3.1-flash-lite-preview",    "gemini_3_1_flash_lite_preview"),
    ("gemma-4-31b-it",                   "gemma_4_31b"),
    ("us.anthropic.claude-opus-4-6-v1",  "claude_opus_4_6"),
    ("us.anthropic.claude-sonnet-4-6",   "claude_sonnet_4_6"),
    ("qwen.qwen3-vl-235b-a22b",         "qwen3_vl_235b_a22b"),
    ("moonshotai.kimi-k2.5",            "kimi_k2_5"),
    ("us.amazon.nova-2-lite-v1:0",      "nova_2_lite"),
    ("qwen/qwen3.5-397b-a17b",         "open_router_qwen3_5_397b_a17b"),
]


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_tier3_2_correct(slug, model_key):
    path = os.path.join(DATA, f"{PREFIX_T32}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    results = {}
    for item in load_json(path):
        if item is None:
            continue
        qs = item.get("tier3_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("pruned_scoring") or {}
        if model_key in scoring:
            results[item["id"]] = scoring[model_key].get("correct", False)
    return results


def get_tier3_correct(slug, model_key):
    path = os.path.join(DATA, f"{PREFIX_T3}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    results = {}
    for item in load_json(path):
        if item is None:
            continue
        qs = item.get("tier3_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("scoring") or {}
        if model_key in scoring:
            results[item["id"]] = scoring[model_key].get("correct", False)
    return results


def get_tier0_correct(slug, model_key):
    path = os.path.join(DATA, f"{PREFIX_T0}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    results = {}
    for item in load_json(path):
        if item is None:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        results[item["id"]] = judge.get("correct", False)
    return results


def main():
    tier3_2_path = os.path.join(DATA, "filtered_data_with_solution_hard_tier3_2.json")
    tier3_2_data = load_json(tier3_2_path)
    tier3_2_ids = set(item["id"] for item in tier3_2_data if item is not None)

    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    p("# Tier 3_2 Evaluation Results (edited + pruned, JPG images)")
    p()
    p(f"Total tier3_2 problems: **{len(tier3_2_ids)}**")
    p()

    # --- Accuracy table ---
    p("## Tier 3_2 Accuracy (judged by gemini-3.1-flash-lite-preview)")
    p()
    p("| Model | Correct | Accuracy |")
    p("|---|---|---|")

    for model_key, slug in MODELS:
        t32 = get_tier3_2_correct(slug, model_key)
        if t32 is None:
            p(f"| {slug} | — | — |")
            continue
        n = len(t32)
        c = sum(1 for v in t32.values() if v)
        p(f"| {slug} | {c}/{n} | {100*c/n:.1f}% |")

    p()

    # --- Comparison: T0 vs T3 vs T3_2 ---
    p("## Comparison: Tier 0 vs Tier 3 vs Tier 3_2")
    p()
    p(f"Accuracy on the same {len(tier3_2_ids)} problems (tier3_2 subset).")
    p()
    p("| Model | Tier 0 | Tier 3 | Tier 3_2 | T0→T3 | T0→T3_2 | T3→T3_2 |")
    p("|---|---|---|---|---|---|---|")

    for model_key, slug in MODELS:
        t0 = get_tier0_correct(slug, model_key)
        t3 = get_tier3_correct(slug, model_key)
        t32 = get_tier3_2_correct(slug, model_key)

        vals = {}
        for label, data_map in [("t0", t0), ("t3", t3), ("t32", t32)]:
            if data_map is None:
                vals[label] = None
                continue
            shared = tier3_2_ids & set(data_map.keys())
            if not shared:
                vals[label] = None
                continue
            acc = 100 * sum(1 for pid in shared if data_map[pid]) / len(shared)
            vals[label] = acc

        def fmt(v):
            return f"{v:.1f}%" if v is not None else "—"

        def delta(a, b):
            if a is not None and b is not None:
                return f"{b-a:+.1f}pp"
            return "—"

        p(f"| {slug} | {fmt(vals['t0'])} | {fmt(vals['t3'])} | {fmt(vals['t32'])} | {delta(vals['t0'], vals['t3'])} | {delta(vals['t0'], vals['t32'])} | {delta(vals['t3'], vals['t32'])} |")

    # --- Build per-problem metadata ---
    item_meta = {}
    for item in tier3_2_data:
        if item is None:
            continue
        qs = item.get("tier3_questions") or []
        if not qs:
            continue
        item_meta[item["id"]] = {
            "relative_difficulty": qs[0].get("relative_difficulty", "unknown"),
            "image_equivalence": qs[0].get("image_equivalence", "unknown"),
        }

    # --- Breakdown by relative_difficulty ---
    difficulty_values = ["same", "easier", "harder"]
    diff_groups = {d: {pid for pid, m in item_meta.items() if m["relative_difficulty"] == d} for d in difficulty_values}

    p("## T0 → T3_2 Breakdown by Relative Difficulty")
    p()
    p(f"Problem counts: same={len(diff_groups['same'])}, easier={len(diff_groups['easier'])}, harder={len(diff_groups['harder'])}")
    p()
    p("| Model | same (T0) | same (T3_2) | same Δ | easier (T0) | easier (T3_2) | easier Δ | harder (T0) | harder (T3_2) | harder Δ |")
    p("|---|---|---|---|---|---|---|---|---|---|")

    for model_key, slug in MODELS:
        t0 = get_tier0_correct(slug, model_key)
        t32 = get_tier3_2_correct(slug, model_key)
        if t0 is None or t32 is None:
            p(f"| {slug} | — | — | — | — | — | — | — | — | — |")
            continue

        parts = []
        for d in difficulty_values:
            ids = diff_groups[d] & set(t0.keys()) & set(t32.keys())
            if not ids:
                parts.extend(["—", "—", "—"])
                continue
            n = len(ids)
            a0 = 100 * sum(1 for pid in ids if t0[pid]) / n
            a32 = 100 * sum(1 for pid in ids if t32[pid]) / n
            parts.extend([f"{a0:.1f}%", f"{a32:.1f}%", f"{a32-a0:+.1f}pp"])

        p(f"| {slug} | {' | '.join(parts)} |")

    p()

    # --- Breakdown by image_equivalence ---
    equiv_values = ["equivalent", "edited"]
    equiv_groups = {e: {pid for pid, m in item_meta.items() if m["image_equivalence"] == e} for e in equiv_values}

    p("## T0 → T3_2 Breakdown by Image Equivalence")
    p()
    p(f"Problem counts: equivalent={len(equiv_groups['equivalent'])}, edited={len(equiv_groups['edited'])}")
    p()
    p("| Model | equiv (T0) | equiv (T3_2) | equiv Δ | edited (T0) | edited (T3_2) | edited Δ |")
    p("|---|---|---|---|---|---|---|")

    for model_key, slug in MODELS:
        t0 = get_tier0_correct(slug, model_key)
        t32 = get_tier3_2_correct(slug, model_key)
        if t0 is None or t32 is None:
            p(f"| {slug} | — | — | — | — | — | — |")
            continue

        parts = []
        for e in equiv_values:
            ids = equiv_groups[e] & set(t0.keys()) & set(t32.keys())
            if not ids:
                parts.extend(["—", "—", "—"])
                continue
            n = len(ids)
            a0 = 100 * sum(1 for pid in ids if t0[pid]) / n
            a32 = 100 * sum(1 for pid in ids if t32[pid]) / n
            parts.extend([f"{a0:.1f}%", f"{a32:.1f}%", f"{a32-a0:+.1f}pp"])

        p(f"| {slug} | {' | '.join(parts)} |")

    p()
    p("## Notes")
    p()
    p("- Tier 3_2 uses pruned questions with regenerated JPG diagrams")
    p("- Pruning removes textual cues that describe diagram content")
    p("- 283 problems after filtering: removed image_has_text (14), rejected (8), both-models-fail (8) from 313")
    p("- **relative_difficulty**: annotator judgment of whether pruning made the problem same/easier/harder")
    p("- **image_equivalence**: whether the regenerated diagram is semantically equivalent or edited from the original")
    p("- Judge model: gemini-3.1-flash-lite-preview")

    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tier3_2_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
