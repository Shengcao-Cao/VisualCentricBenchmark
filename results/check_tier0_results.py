"""Check tier0 (original image) evaluation results from filtered_data_with_solution_hard_*_judged.json."""

import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def main():
    lines = []

    def p(s=""):
        print(s)
        lines.append(s)

    p("# Tier 0 Evaluation Results (Original Images)")
    p()
    p("Results from `filtered_data_with_solution_hard_[model]_judged.json`.")
    p("Judge model: gemini-3.1-flash-lite-preview.")
    p()

    # --- Overall accuracy ---
    p("## Overall Accuracy")
    p()
    p("| Model | Total | Correct | Incorrect | Parse Errors | Accuracy |")
    p("|---|---|---|---|---|---|")

    all_results = {}  # slug -> {id: correct}

    for model_key, slug in MODELS:
        path = os.path.join(BASE, "data", f"filtered_data_with_solution_hard_{slug}_judged.json")
        if not os.path.exists(path):
            p(f"| {slug} | N/A | N/A | N/A | N/A | N/A |")
            continue

        data = load_json(path)
        total = correct = incorrect = parse_errors = 0
        results_by_id = {}

        for item in data:
            if item is None:
                continue
            pid = item.get("id")
            judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
            if not judge:
                continue
            total += 1
            reasoning = judge.get("reasoning", "")
            if "Parse error" in reasoning:
                parse_errors += 1
                results_by_id[pid] = False
            elif judge.get("correct"):
                correct += 1
                results_by_id[pid] = True
            else:
                incorrect += 1
                results_by_id[pid] = False

        all_results[slug] = results_by_id
        acc = 100 * correct / total if total else 0
        p(f"| {slug} | {total} | {correct} | {incorrect} | {parse_errors} | {acc:.1f}% |")

    p()

    # --- By question type ---
    p("## Accuracy by Question Type")
    p()
    p("| Model | single_selection | free_form |")
    p("|---|---|---|")

    for model_key, slug in MODELS:
        path = os.path.join(BASE, "data", f"filtered_data_with_solution_hard_{slug}_judged.json")
        if not os.path.exists(path):
            p(f"| {slug} | N/A | N/A |")
            continue

        data = load_json(path)
        by_type = {}

        for item in data:
            if item is None:
                continue
            judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
            if not judge:
                continue
            qt = item.get("question_type", "unknown")
            by_type.setdefault(qt, {"correct": 0, "total": 0})
            by_type[qt]["total"] += 1
            if judge.get("correct"):
                by_type[qt]["correct"] += 1

        parts = []
        for qt in ["single_selection", "free_form"]:
            if qt in by_type and by_type[qt]["total"] > 0:
                acc = 100 * by_type[qt]["correct"] / by_type[qt]["total"]
                parts.append(f"{by_type[qt]['correct']}/{by_type[qt]['total']} ({acc:.1f}%)")
            else:
                parts.append("N/A")
        p(f"| {slug} | {parts[0]} | {parts[1]} |")

    p()

    # --- By domain ---
    p("## Accuracy by Domain (top domains)")
    p()

    # Collect domain stats across all models
    # First pass: find domains
    sample_path = os.path.join(BASE, "data", f"filtered_data_with_solution_hard_{MODELS[0][1]}_judged.json")
    sample_data = load_json(sample_path)
    domain_counts = Counter(item.get("domain", "unknown") for item in sample_data if item is not None)
    top_domains = [d for d, _ in domain_counts.most_common(8)]

    header = "| Model | " + " | ".join(top_domains) + " |"
    sep = "|---|" + "|".join(["---"] * len(top_domains)) + "|"
    p(header)
    p(sep)

    for model_key, slug in MODELS:
        path = os.path.join(BASE, "data", f"filtered_data_with_solution_hard_{slug}_judged.json")
        if not os.path.exists(path):
            continue

        data = load_json(path)
        by_domain = {}
        for item in data:
            if item is None:
                continue
            judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
            if not judge:
                continue
            domain = item.get("domain", "unknown")
            by_domain.setdefault(domain, {"correct": 0, "total": 0})
            by_domain[domain]["total"] += 1
            if judge.get("correct"):
                by_domain[domain]["correct"] += 1

        parts = []
        for d in top_domains:
            if d in by_domain and by_domain[d]["total"] > 0:
                acc = 100 * by_domain[d]["correct"] / by_domain[d]["total"]
                parts.append(f"{acc:.0f}%")
            else:
                parts.append("N/A")
        p(f"| {slug} | " + " | ".join(parts) + " |")

    p()

    # --- By dataset ---
    p("## Accuracy by Source Dataset")
    p()

    dataset_counts = Counter(item.get("dataset", "unknown") for item in sample_data if item is not None)
    top_datasets = [d for d, _ in dataset_counts.most_common()]

    header = "| Model | " + " | ".join(top_datasets) + " |"
    sep = "|---|" + "|".join(["---"] * len(top_datasets)) + "|"
    p(header)
    p(sep)

    for model_key, slug in MODELS:
        path = os.path.join(BASE, "data", f"filtered_data_with_solution_hard_{slug}_judged.json")
        if not os.path.exists(path):
            continue

        data = load_json(path)
        by_ds = {}
        for item in data:
            if item is None:
                continue
            judge = (item.get("model") or {}).get(model_key, {}).get("judge") or {}
            if not judge:
                continue
            ds = item.get("dataset", "unknown")
            by_ds.setdefault(ds, {"correct": 0, "total": 0})
            by_ds[ds]["total"] += 1
            if judge.get("correct"):
                by_ds[ds]["correct"] += 1

        parts = []
        for ds in top_datasets:
            if ds in by_ds and by_ds[ds]["total"] > 0:
                acc = 100 * by_ds[ds]["correct"] / by_ds[ds]["total"]
                parts.append(f"{acc:.0f}%")
            else:
                parts.append("N/A")
        p(f"| {slug} | " + " | ".join(parts) + " |")

    p()
    p("## Notes")
    p()
    p(f"- Total problems: {domain_counts.total()}")
    p(f"- Domain distribution: {', '.join(f'{d} ({c})' for d, c in domain_counts.most_common())}")
    p(f"- Dataset distribution: {', '.join(f'{d} ({c})' for d, c in dataset_counts.most_common())}")
    p("- Judge model: gemini-3.1-flash-lite-preview")

    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tier0_results.md")
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved to {md_path}")


if __name__ == "__main__":
    main()
