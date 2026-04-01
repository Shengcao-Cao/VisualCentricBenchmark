"""Merge additional model results into filtered_data_with/without_solution.json.

Usage:
    python merge_solutions.py <result_file>:<model_key> [<result_file>:<model_key> ...]

Example:
    python merge_solutions.py \\
        coreset/filtered_data_without_solution_gpt_5_4.json:gpt-5.4 \\
        coreset/filtered_data_without_solution_gemini_3_1_pro_preview.json:gemini-3.1-pro-preview

Each model result file should be a JSON list with the same schema as
filtered_data_without_solution.json, containing model entries under
the `model` field. Only the entry matching the specified model_key is
merged from each file.

The script:

1. Reads the current filtered_data_with_solution.json and filtered_data_without_solution.json
2. For each model result file, merges the specified model's entries into the without-solution items
3. Picks the best correct model answer (by accuracy across new models, strongest first)
4. Moves newly solvable items to with_solution, keeps the rest in without_solution
5. Overwrites both output files
"""

import json
import sys
from collections import Counter

BASE = "/Users/shengcao/Downloads/formalized_datasets/coreset"
WITH_PATH = f"{BASE}/filtered_data_with_solution.json"
WITHOUT_PATH = f"{BASE}/filtered_data_without_solution.json"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <result_file>:<model_key> [...]")
        sys.exit(1)

    # Parse file:model_key pairs
    model_result_pairs = []
    for arg in sys.argv[1:]:
        if ":" not in arg:
            print(f"Error: expected <result_file>:<model_key>, got: {arg}")
            sys.exit(1)
        # Split on last colon to allow colons in file paths
        fpath, model_key = arg.rsplit(":", 1)
        model_result_pairs.append((fpath, model_key))

    # Load current state
    with open(WITH_PATH) as f:
        with_solution = json.load(f)
    with open(WITHOUT_PATH) as f:
        without_solution = json.load(f)

    print(f"Current: {len(with_solution)} with solution, {len(without_solution)} without")

    # Index without_solution by id for merging
    without_by_id = {item["id"]: item for item in without_solution}

    # Collect all new model names and their accuracy for priority ranking
    new_model_stats = Counter()  # model_name -> correct count
    new_model_totals = Counter()  # model_name -> total count
    # Merge model entries from each result file
    for fpath, model_key in model_result_pairs:
        print(f"\nMerging {fpath} (model: {model_key})...")
        with open(fpath) as f:
            results = json.load(f)

        merged = 0
        for result_item in results:
            item_id = result_item["id"]
            if item_id not in without_by_id:
                continue
            target = without_by_id[item_id]
            model_entry = result_item.get("model", {}).get(model_key)
            if model_entry is None:
                continue
            target.setdefault("model", {})[model_key] = model_entry
            new_model_totals[model_key] += 1
            if model_entry.get("judge", {}).get("correct", False):
                new_model_stats[model_key] += 1
            merged += 1
        print(f"  Merged {merged} model entries")

    # Rank new models by accuracy (highest first)
    model_priority = sorted(
        new_model_stats.keys(),
        key=lambda m: new_model_stats[m] / max(new_model_totals[m], 1),
        reverse=True,
    )
    # Include models with 0 correct that appeared in totals
    for m in new_model_totals:
        if m not in model_priority:
            model_priority.append(m)

    print("\nNew model priority (by accuracy):")
    for m in model_priority:
        acc = new_model_stats[m] / max(new_model_totals[m], 1)
        print(f"  {m}: {new_model_stats[m]}/{new_model_totals[m]} ({100*acc:.1f}%)")

    # Try to assign solutions from new models
    newly_solved = []
    still_unsolved = []
    source_counts = Counter()

    for item in without_solution:
        solved = False
        for model_name in model_priority:
            entry = item.get("model", {}).get(model_name, {})
            judge = entry.get("judge", {})
            if judge.get("correct"):
                answer = entry.get("answer", "")
                if answer and isinstance(answer, str) and answer.strip():
                    item["solution"] = answer.strip()
                    item["solution_source"] = f"model:{model_name}"
                    source_counts[model_name] += 1
                    newly_solved.append(item)
                    solved = True
                    break
        if not solved:
            still_unsolved.append(item)

    print(f"\nNewly solved: {len(newly_solved)}")
    for m, c in source_counts.most_common():
        print(f"  {m}: {c}")
    print(f"Still unsolved: {len(still_unsolved)}")

    # Update output files
    updated_with = with_solution + newly_solved
    with open(WITH_PATH, "w") as f:
        json.dump(updated_with, f, indent=2, ensure_ascii=False)

    with open(WITHOUT_PATH, "w") as f:
        json.dump(still_unsolved, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated: {len(updated_with)} with solution, {len(still_unsolved)} without")


if __name__ == "__main__":
    main()
