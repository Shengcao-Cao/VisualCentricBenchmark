"""Check tier1 evaluation results: accuracy vs majority vote, by model and question type."""

import json
import glob
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "filtered_data_with_solution_hard_tier1+2_clean_tier1_"

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

# Tier1 question types
TYPE_NAMES = {
    "A": "Entity Recognition",
    "B": "Spatial Reasoning",
    "C": "Attribute Identification",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def check_model(model_key, slug):
    """Return stats for a model's tier1 predictions vs majority vote."""
    path = os.path.join(BASE, "data", f"{PREFIX}{slug}.json")
    if not os.path.exists(path):
        return None

    data = load_json(path)

    total_items = len([d for d in data if d is not None])
    total_qs = 0
    answered = 0
    correct = 0
    no_majority = 0

    by_type = {}  # type -> {correct, total}

    for item in data:
        if item is None:
            continue
        for q in item.get("tier1_questions") or []:
            total_qs += 1
            gt = q.get("gt_answer") or (q.get("reference_answers") or {}).get("majority_vote")
            pred = (q.get("predictions") or {}).get(model_key)

            if not gt:
                no_majority += 1
                continue

            qtype = q.get("type", "?")
            by_type.setdefault(qtype, {"correct": 0, "total": 0})

            if pred:
                answered += 1
                by_type[qtype]["total"] += 1
                if pred == gt:
                    correct += 1
                    by_type[qtype]["correct"] += 1
            else:
                by_type[qtype]["total"] += 1

    return {
        "total_items": total_items,
        "total_qs": total_qs,
        "answered": answered,
        "correct": correct,
        "no_majority": no_majority,
        "by_type": by_type,
    }


def main():
    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    # Get total from source file
    src_path = os.path.join(BASE, "data", "filtered_data_with_solution_hard_tier1+2_clean.json")
    src_data = load_json(src_path)
    total_items = len(src_data)
    total_qs = sum(len(d.get("tier1_questions") or []) for d in src_data)

    p("# Tier 1 Evaluation Results")
    p()
    p(f"Total items: **{total_items}**, total sub-questions: **{total_qs}**")
    p()
    p("Accuracy is measured against the ground truth answer (majority vote for")
    p("unanimous items, human-annotated answer for reviewed items).")
    p()

    # --- Overall accuracy ---
    p("## Overall Accuracy")
    p()
    p("| Model | Items | Questions | Answered | Correct | Accuracy |")
    p("|---|---|---|---|---|---|")

    all_stats = {}
    for model_key, slug in MODELS:
        stats = check_model(model_key, slug)
        if stats is None:
            p(f"| {slug} | — | — | — | — | — |")
            continue
        all_stats[slug] = stats
        acc = 100 * stats["correct"] / stats["answered"] if stats["answered"] else 0
        p(f"| {slug} | {stats['total_items']} | {stats['total_qs']} | {stats['answered']} | {stats['correct']} | {acc:.1f}% |")

    p()

    # --- By question type ---
    p("## Accuracy by Question Type")
    p()
    header = "| Model |"
    sep = "|---|"
    for t in ("A", "B", "C"):
        header += f" {t}: {TYPE_NAMES[t]} |"
        sep += "---|"
    p(header)
    p(sep)

    for model_key, slug in MODELS:
        stats = all_stats.get(slug)
        if stats is None:
            p(f"| {slug} |" + " — |" * 3)
            continue
        parts = []
        for t in ("A", "B", "C"):
            bt = stats["by_type"].get(t, {"correct": 0, "total": 0})
            if bt["total"] > 0:
                acc = 100 * bt["correct"] / bt["total"]
                parts.append(f"{bt['correct']}/{bt['total']} ({acc:.1f}%)")
            else:
                parts.append("—")
        p(f"| {slug} | " + " | ".join(parts) + " |")

    p()
    p("## Notes")
    p()
    p("- Tier1 questions are simple MCQ (A/B/C/D) about visual perception")
    p("- No LLM judge needed — direct comparison against ground truth")
    p("- Ground truth: majority vote (unanimous items) or human annotation (reviewed items)")
    p("- Thinking disabled for all models (perception-only, no reasoning required)")
    p(f"- Question type distribution: {', '.join(f'{t} ({TYPE_NAMES[t]})' for t in ('A', 'B', 'C'))}")

    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tier1_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
