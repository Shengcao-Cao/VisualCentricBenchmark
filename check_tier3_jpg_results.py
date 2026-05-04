"""Check tier3 JPG evaluation results: accuracy, unreadable complaints, and comparison with PNG and original."""

import json
import os
import re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
PREFIX_JPG = "filtered_data_with_solution_hard_tier3_jpg_"
PREFIX_PNG = "filtered_data_with_solution_hard_tier3_"

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


def check_judged(prefix, slug, tier_key="tier3_questions"):
    path = os.path.join(BASE, f"{prefix}{slug}_judged.json")
    if not os.path.exists(path):
        return None
    data = load_json(path)
    correct = incorrect = parse_errors = done = 0
    for item in data:
        if item is None:
            continue
        qs = item.get(tier_key) or []
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


def check_unreadable(prefix, slug, tier_key="tier3_questions"):
    path = os.path.join(BASE, f"{prefix}{slug}.json")
    if not os.path.exists(path):
        return set()
    data = load_json(path)
    ids = set()
    for item in data:
        if item is None:
            continue
        qs = item.get(tier_key) or []
        if not qs:
            continue
        preds = qs[0].get("predictions") or {}
        for mk, pred_text in preds.items():
            if isinstance(pred_text, str) and UNREADABLE_RE.search(pred_text):
                ids.add(item["id"])
    return ids


def get_original_correct(model_key, slug, tier3_ids):
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
    tier3_path = os.path.join(BASE, "filtered_data_with_solution_hard_tier3_fixed_jpg.json")
    tier3_data = load_json(tier3_path)
    tier3_ids = set(item["id"] for item in tier3_data if item is not None)

    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    p("# Tier 3 Evaluation Results (JPG images)")
    p()
    p(f"Total tier3 problems: **{len(tier3_ids)}**")
    p()

    # --- Accuracy table: JPG vs PNG ---
    p("## Accuracy (judged by gemini-3.1-flash-lite-preview)")
    p()
    p("| Model | JPG Correct | JPG Acc | PNG Acc | JPG-PNG |")
    p("|---|---|---|---|---|")

    jpg_acc = {}
    png_acc = {}
    for model_key, slug in MODELS:
        jpg_result = check_judged(PREFIX_JPG, slug)
        png_result = check_judged(PREFIX_PNG, slug)

        if jpg_result:
            done, correct, incorrect, _ = jpg_result
            ja = 100 * correct / done if done else 0
            jpg_acc[slug] = ja
            jpg_str = f"{correct}/{done}"
            ja_str = f"{ja:.1f}%"
        else:
            jpg_str = ja_str = "—"
            ja = None

        if png_result:
            done, correct, _, _ = png_result
            pa = 100 * correct / done if done else 0
            png_acc[slug] = pa
            pa_str = f"{pa:.1f}%"
        else:
            pa_str = "—"
            pa = None

        if ja is not None and pa is not None:
            delta = ja - pa
            delta_str = f"{delta:+.1f}%"
        else:
            delta_str = "—"

        p(f"| {slug} | {jpg_str} | {ja_str} | {pa_str} | {delta_str} |")

    p()

    # --- Unreadable complaints: JPG vs PNG ---
    p("## Unreadable image complaints (JPG vs PNG)")
    p()
    p("| Model | JPG | PNG | Reduction |")
    p("|---|---|---|---|")

    for model_key, slug in MODELS:
        jpg_ids = check_unreadable(PREFIX_JPG, slug)
        png_ids = check_unreadable(PREFIX_PNG, slug)

        if png_ids:
            reduction = len(png_ids) - len(jpg_ids)
            pct = 100 * reduction / len(png_ids) if png_ids else 0
            red_str = f"-{reduction} ({pct:.0f}%)"
        else:
            red_str = "—"

        p(f"| {slug} | {len(jpg_ids)} | {len(png_ids)} | {red_str} |")

    p()

    # --- Comparison with original images ---
    p("## Comparison with original images (tier0)")
    p()
    p(f"Accuracy on the same {len(tier3_ids)} problems.")
    p()
    p("| Model | Original | JPG | PNG | Orig→JPG | Orig→PNG |")
    p("|---|---|---|---|---|---|")

    for model_key, slug in MODELS:
        orig_correct = get_original_correct(model_key, slug, tier3_ids)

        # JPG correct
        jpg_path = os.path.join(BASE, f"{PREFIX_JPG}{slug}_judged.json")
        jpg_correct = {}
        if os.path.exists(jpg_path):
            for item in load_json(jpg_path):
                if item is None:
                    continue
                qs = item.get("tier3_questions") or []
                if qs:
                    for mk, r in (qs[0].get("scoring") or {}).items():
                        jpg_correct[item["id"]] = r.get("correct", False)

        # PNG correct
        png_path = os.path.join(BASE, f"{PREFIX_PNG}{slug}_judged.json")
        png_correct = {}
        if os.path.exists(png_path):
            for item in load_json(png_path):
                if item is None:
                    continue
                qs = item.get("tier3_questions") or []
                if qs:
                    for mk, r in (qs[0].get("scoring") or {}).items():
                        png_correct[item["id"]] = r.get("correct", False)

        if orig_correct is None:
            p(f"| {slug} | — | — | — | — | — |")
            continue

        shared = set(orig_correct.keys()) & set(jpg_correct.keys()) & set(png_correct.keys())
        if not shared:
            p(f"| {slug} | — | — | — | — | — |")
            continue

        oa = 100 * sum(1 for pid in shared if orig_correct[pid]) / len(shared)
        ja = 100 * sum(1 for pid in shared if jpg_correct[pid]) / len(shared)
        pa = 100 * sum(1 for pid in shared if png_correct[pid]) / len(shared)

        p(f"| {slug} | {oa:.1f}% | {ja:.1f}% | {pa:.1f}% | {ja-oa:+.1f}% | {pa-oa:+.1f}% |")

    p()
    p("## Notes")
    p()
    p("- JPG images have white backgrounds (no transparency)")
    p("- PNG images had transparent backgrounds (RGBA), causing \"blank/black\" complaints")
    p("- Judge model: gemini-3.1-flash-lite-preview")

    md_path = os.path.join(BASE, "tier3_jpg_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
