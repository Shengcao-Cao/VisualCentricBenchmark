"""Filter out problems that are too easy for all models, with optional
difficulty-based splits.

A problem is removed if EITHER condition is met:
  1. All models answered correctly (judge.correct == True for every model).
  2. All models rated difficulty <= 3.

With --splits, remaining problems are bucketed into difficulty tiers
based on how many models answered correctly:
  - hard:   0 models correct
  - medium: 1 model correct
  - easy:   2 models correct
Each split is saved to <output_stem>_<split>.json.

Accepts multiple input files. When more than one file is given, model data
is merged by problem ID (only problems present in ALL inputs are kept).

Usage:
    python filter_easy.py --input a.json b.json c.json --output filtered.json
    python filter_easy.py --input a.json b.json c.json --output filtered.json --splits

Defaults:
    --output filtered_data.json
"""

import argparse
import json
import re
from pathlib import Path


def detect_language(item: dict) -> str:
    """Detect language from question text: 'zh' or 'en'."""
    question = item.get("question", "")
    if len(re.findall(r"[\u4e00-\u9fff]", question)) > 5:
        return "zh"
    return "en"


def difficulty_split(item: dict) -> str:
    """Assign a difficulty split based on number of models correct."""
    models = item["model"]
    n_correct = sum(
        1 for m in models.values() if m.get("judge", {}).get("correct") is True
    )
    if n_correct == 0:
        return "hard"
    if n_correct == 1:
        return "medium"
    return "easy"


def is_too_easy(item: dict) -> bool:
    """Return True if the problem should be removed (too easy)."""
    models = item.get("model", {})
    if not models:
        return False

    all_correct = all(
        m.get("judge", {}).get("correct") is True for m in models.values()
    )
    all_low_difficulty = all(
        m.get("difficulty", {}).get("difficulty", 99) <= 3 for m in models.values()
    )
    return all_correct or all_low_difficulty


def load_and_merge(paths: list[str]) -> list[dict]:
    """Load one or more JSON files and merge model data by problem ID.

    When multiple files are given, only problems present in ALL files are kept.
    The model dicts are merged so each problem has all models' results.
    """
    datasets = []
    for path in paths:
        with open(path) as f:
            datasets.append(json.load(f))
        print(f"Loaded {len(datasets[-1])} items from {path}")

    if len(datasets) == 1:
        return datasets[0]

    # Build ID -> item lookup for each dataset
    id_maps: list[dict[str, dict]] = []
    for ds in datasets:
        by_id = {}
        for item in ds:
            if item and isinstance(item, dict) and "id" in item:
                by_id[item["id"]] = item
        id_maps.append(by_id)

    # Intersect problem IDs across all datasets
    common_ids = set(id_maps[0].keys())
    for m in id_maps[1:]:
        common_ids &= m.keys()

    # Use first dataset's order, merge model dicts from all datasets
    merged = []
    for item in datasets[0]:
        if not (item and isinstance(item, dict) and item.get("id") in common_ids):
            continue
        combined_models = {}
        for m in id_maps:
            combined_models.update(m[item["id"]].get("model", {}))
        result = {k: v for k, v in item.items() if k != "model"}
        if combined_models:
            result["model"] = combined_models
        merged.append(result)

    print(f"Merged: {len(merged)} problems (intersection of {len(datasets)} files)")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", nargs="+", required=True, help="Input JSON file(s)"
    )
    parser.add_argument(
        "--output", default="filtered_data.json", help="Output JSON file"
    )
    parser.add_argument(
        "--splits",
        action="store_true",
        help="Also output difficulty splits (hard/medium/easy)",
    )
    args = parser.parse_args()

    data = load_and_merge(args.input)

    kept = [item for item in data if not is_too_easy(item)]
    for item in kept:
        item["language"] = detect_language(item)
    removed = len(data) - len(kept)

    print(f"Total: {len(data)}")
    print(f"Removed (too easy): {removed}")
    print(f"Kept: {len(kept)}")

    with open(args.output, "w") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    print(f"Saved to {args.output}")

    if args.splits:
        splits: dict[str, list[dict]] = {"hard": [], "medium": [], "easy": []}
        for item in kept:
            splits[difficulty_split(item)].append(item)

        stem = Path(args.output).stem
        parent = Path(args.output).parent
        for split_name, items in splits.items():
            split_path = parent / f"{stem}_{split_name}.json"
            with open(split_path, "w") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            print(f"  {split_name}: {len(items)} -> {split_path}")


if __name__ == "__main__":
    main()
