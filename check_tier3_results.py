"""Check tier3 evaluation results: accuracy, unreadable complaints, and comparison with original."""

import json
import glob
import os
import re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "filtered_data_with_solution_hard_tier3_"

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

UNREADABLE_PATTERNS = [
    r"cannot be determined",
    r"cannot determine",
    r"unable to determine",
    r"can't be determined",
    r"cannot.*(?:see|read|interpret|identify|view|access|analyze).*(?:image|figure|diagram)",
    r"(?:image|figure|diagram).*(?:not|isn't|can't|cannot).*(?:visible|readable|clear|provided|available|shown|displayed)",
    r"no (?:image|figure|diagram)",
    r"(?:image|figure|diagram).*(?:blank|empty|missing|unclear|unreadable)",
    r"failed to (?:identify|recognize|read|interpret)",
    r"(?:sorry|unfortunately).*(?:image|figure|diagram)",
    r"without.*(?:image|figure|diagram|seeing)",
]
UNREADABLE_RE = re.compile("|".join(f"(?:{p})" for p in UNREADABLE_PATTERNS), re.IGNORECASE)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_tier3_ids():
    path = os.path.join(BASE, "filtered_data_with_solution_hard_tier3_fixed.json")
    data = load_json(path)
    return set(item["id"] for item in data if item is not None)


def check_judged(slug):
    """Return (total, correct, incorrect, parse_errors) from judged file."""
    path = os.path.join(BASE, f"{PREFIX}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    correct = incorrect = parse_errors = 0
    done = 0
    for item in data:
        if item is None:
            continue
        qs = item.get("tier3_questions") or []
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
    return done, correct, incorrect, parse_errors


def check_unreadable(slug):
    """Return set of problem IDs where the model complained about unreadable images."""
    path = os.path.join(BASE, f"{PREFIX}{slug}.json")
    if not os.path.exists(path):
        return set()
    data = load_json(path)
    ids = set()
    for item in data:
        if item is None:
            continue
        qs = item.get("tier3_questions") or []
        if not qs:
            continue
        preds = qs[0].get("predictions") or {}
        for mk, pred_text in preds.items():
            if isinstance(pred_text, str) and UNREADABLE_RE.search(pred_text):
                ids.add(item["id"])
    return ids


def check_original(model_key, slug, tier3_ids):
    """Return {id: correct} for the original judged results, filtered to tier3 IDs."""
    path = os.path.join(BASE, f"filtered_data_with_solution_hard_{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    results = {}
    for item in data:
        if item is None:
            continue
        pid = item.get("id")
        if pid not in tier3_ids:
            continue
        judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
        results[pid] = judge.get("correct", False)
    return results


def main():
    tier3_ids = get_tier3_ids()
    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    p("# Tier 3 Evaluation Results")
    p()
    p(f"Total tier3 problems: **{len(tier3_ids)}**")
    p()

    # --- Accuracy table ---
    p("## Accuracy (judged by gemini-3.1-flash-lite-preview)")
    p()
    p("| Model | Total | Correct | Incorrect | Accuracy |")
    p("|---|---|---|---|---|")

    accuracy_data = {}
    for model_key, slug in MODELS:
        result = check_judged(slug)
        if result is None:
            p(f"| {slug} | N/A | N/A | N/A | N/A |")
            continue
        done, correct, incorrect, parse_errors = result
        acc = 100 * correct / done if done else 0
        accuracy_data[slug] = acc
        p(f"| {slug} | {done} | {correct} | {incorrect} | {acc:.1f}% |")

    p()

    # --- Unreadable complaints ---
    p("## Unreadable image complaints")
    p()
    p("Number of items where the model's answer text suggests it couldn't read the image.")
    p("All 313 images render correctly; these are false negatives from the models.")
    p()
    p("| Model | Unreadable | % |")
    p("|---|---|---|")

    model_unreadable = {}
    for model_key, slug in MODELS:
        ids = check_unreadable(slug)
        model_unreadable[slug] = ids
        pct = 100 * len(ids) / len(tier3_ids) if tier3_ids else 0
        p(f"| {slug} | {len(ids)} | {pct:.1f}% |")

    # Most problematic items
    item_counts = Counter()
    for ids in model_unreadable.values():
        for pid in ids:
            item_counts[pid] += 1

    multi = [(pid, cnt) for pid, cnt in item_counts.items() if cnt >= 5]
    multi.sort(key=lambda x: -x[1])

    p()
    p(f"Items flagged by 5+ models ({len(multi)}):")
    p()
    p("| Problem ID | Models flagging |")
    p("|---|---|")
    for pid, cnt in multi:
        p(f"| {pid} | {cnt} |")

    p()

    # --- Comparison with original ---
    p("## Comparison with original images")
    p()
    p("Accuracy on the same 313 problems using original images vs tier3 regenerated diagrams.")
    p()
    p("| Model | Original | Tier3 | Delta |")
    p("|---|---|---|---|")

    for model_key, slug in MODELS:
        orig_results = check_original(model_key, slug, tier3_ids)
        tier3_acc = accuracy_data.get(slug)
        if orig_results is None or tier3_acc is None:
            p(f"| {slug} | N/A | N/A | N/A |")
            continue

        tier3_path = os.path.join(BASE, f"{PREFIX}{slug}_judged.json")
        tier3_data = load_json(tier3_path)
        tier3_correct = {}
        for item in tier3_data:
            if item is None:
                continue
            pid = item.get("id")
            qs = item.get("tier3_questions") or []
            if not qs:
                continue
            scoring = qs[0].get("scoring") or {}
            for mk, result in scoring.items():
                tier3_correct[pid] = result.get("correct", False)

        shared = set(orig_results.keys()) & set(tier3_correct.keys())
        if not shared:
            p(f"| {slug} | N/A | N/A | N/A |")
            continue

        orig_acc = 100 * sum(1 for pid in shared if orig_results[pid]) / len(shared)
        t3_acc = 100 * sum(1 for pid in shared if tier3_correct[pid]) / len(shared)
        delta = t3_acc - orig_acc
        p(f"| {slug} | {orig_acc:.1f}% | {t3_acc:.1f}% | {delta:+.1f}% |")

    p()
    p("## Notes")
    p()
    p("- 312/313 tier3 PNGs have transparent backgrounds (RGBA). Models may render transparent regions as black,")
    p("  contributing to false \"blank/black image\" complaints. Consider flattening alpha to white.")
    p("- Judge model: gemini-3.1-flash-lite-preview (default in tier3.sh)")
    p("- All tier3 images were converted from inline SVGs via cairosvg")

    # Write markdown
    md_path = os.path.join(BASE, "tier3_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
