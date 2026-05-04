"""Check tier2 evaluation results: accuracy and comparison with original (tier0)."""

import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "no_review_needed_substantive_tier2_"

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


def get_tier2_ids():
    path = os.path.join(BASE, "data", "no_review_needed_substantive.json")
    data = load_json(path)
    return set(item["id"] for item in data if item is not None)


def check_judged(slug):
    """Return (total, done, correct, incorrect, parse_errors) from judged file."""
    path = os.path.join(BASE, "data", "data", f"{PREFIX}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    total = len(data)
    correct = incorrect = parse_errors = 0
    done = 0
    for item in data:
        if item is None:
            continue
        qs = item.get("tier2_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("scoring") or {}
        if not scoring:
            continue
        done += 1
        for mk, result in scoring.items():
            if "Parse error" in result.get("reasoning", ""):
                parse_errors += 1
            elif result.get("correct"):
                correct += 1
            else:
                incorrect += 1
    return total, done, correct, incorrect, parse_errors


def check_judged_by_type(slug):
    """Return {question_type: {correct, total}} from judged file."""
    path = os.path.join(BASE, "data", "data", f"{PREFIX}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    by_type = {}
    for item in data:
        if item is None:
            continue
        qs = item.get("tier2_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("scoring") or {}
        if not scoring:
            continue
        qt = item.get("question_type", "unknown")
        by_type.setdefault(qt, {"correct": 0, "total": 0})
        by_type[qt]["total"] += 1
        for mk, result in scoring.items():
            if result.get("correct"):
                by_type[qt]["correct"] += 1
    return by_type


def get_tier2_correct(slug):
    """Return {id: correct} for tier2 judged results."""
    path = os.path.join(BASE, "data", "data", f"{PREFIX}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    results = {}
    for item in data:
        if item is None:
            continue
        pid = item.get("id")
        qs = item.get("tier2_questions") or []
        if not qs:
            continue
        scoring = qs[0].get("scoring") or {}
        for mk, result in scoring.items():
            results[pid] = result.get("correct", False)
    return results


def get_original_correct(model_key, slug, tier2_ids):
    """Return {id: correct} for original judged results, filtered to tier2 IDs."""
    path = os.path.join(BASE, "data", "data", f"filtered_data_with_solution_hard_{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    results = {}
    for item in data:
        if item is None:
            continue
        pid = item.get("id")
        if pid not in tier2_ids:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        results[pid] = judge.get("correct", False)
    return results


def main():
    tier2_ids = get_tier2_ids()
    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    p("# Tier 2 Evaluation Results")
    p()
    p(f"Total tier2 substantive problems: **{len(tier2_ids)}**")
    p()

    # --- Accuracy table ---
    p("## Accuracy (judged by gemini-3.1-flash-lite-preview)")
    p()
    p("| Model | Total | Done | Correct | Incorrect | Accuracy |")
    p("|---|---|---|---|---|---|")

    accuracy_data = {}
    for model_key, slug in MODELS:
        result = check_judged(slug)
        if result is None:
            p(f"| {slug} | — | — | — | — | — |")
            continue
        total, done, correct, incorrect, parse_errors = result
        acc = 100 * correct / done if done else 0
        accuracy_data[slug] = (done, acc)
        status = "" if done == total else f" ({done}/{total})"
        p(f"| {slug} | {total} | {done}{status} | {correct} | {incorrect} | {acc:.1f}% |")

    p()

    # --- By question type ---
    p("## Accuracy by Question Type")
    p()
    p("| Model | single_selection | free_form |")
    p("|---|---|---|")

    for model_key, slug in MODELS:
        by_type = check_judged_by_type(slug)
        if by_type is None:
            p(f"| {slug} | — | — |")
            continue
        parts = []
        for qt in ["single_selection", "free_form"]:
            if qt in by_type and by_type[qt]["total"] > 0:
                acc = 100 * by_type[qt]["correct"] / by_type[qt]["total"]
                parts.append(f"{by_type[qt]['correct']}/{by_type[qt]['total']} ({acc:.1f}%)")
            else:
                parts.append("—")
        p(f"| {slug} | {parts[0]} | {parts[1]} |")

    p()

    # --- Comparison with original ---
    p("## Comparison with original (tier0)")
    p()
    p(f"Accuracy on the same {len(tier2_ids)} problems: original question vs tier2 pruned question.")
    p()
    p("| Model | Original | Tier2 | Delta |")
    p("|---|---|---|---|")

    for model_key, slug in MODELS:
        t2_correct = get_tier2_correct(slug)
        orig_correct = get_original_correct(model_key, slug, tier2_ids)

        if t2_correct is None or orig_correct is None:
            p(f"| {slug} | — | — | — |")
            continue

        shared = set(t2_correct.keys()) & set(orig_correct.keys())
        if not shared:
            p(f"| {slug} | — | — | — |")
            continue

        orig_acc = 100 * sum(1 for pid in shared if orig_correct[pid]) / len(shared)
        t2_acc = 100 * sum(1 for pid in shared if t2_correct[pid]) / len(shared)
        delta = t2_acc - orig_acc
        p(f"| {slug} | {orig_acc:.1f}% | {t2_acc:.1f}% | {delta:+.1f}% |")

    p()
    p("## Notes")
    p()
    p(f"- Substantive tier2 problems: {len(tier2_ids)} (after filtering {657} trivial rewrites from {len(tier2_ids)+657})")
    p("- Tier2 uses pruned questions with original images")
    p("- Judge model: gemini-3.1-flash-lite-preview")

    # Write markdown
    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tier2_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
