"""Consolidate annotated tier3 pruned data into a single cleaned file.

Aggregates 5 annotator shards, filters out rejected/image-has-text items and
problems where both GPT-5.4 and Gemini-3.1-Pro fail the original, restructures
tier3_pruned_questions into tier3_questions, and fixes question_type mismatches.
"""

import argparse
import json
from pathlib import Path

ANNOTATORS = ["david", "ji", "mingye", "shengcao", "zheyu"]
INPUT_TEMPLATE = "data/filtered_data_with_solution_hard_tier3_jpg_pruned_fixed_{}.json"
GPT_JUDGED = "data/filtered_data_with_solution_hard_gpt_5_4_judged.json"
GEMINI_JUDGED = "data/filtered_data_with_solution_hard_gemini_3_1_pro_preview_judged.json"
DEFAULT_OUTPUT = "data/filtered_data_with_solution_hard_tier3_2.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolidate annotated tier3 pruned data")
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT, help="Output JSON path"
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent

    # Load & aggregate annotator files
    all_items: list[dict] = []
    for name in ANNOTATORS:
        path = root / INPUT_TEMPLATE.format(name)
        items = json.loads(path.read_text())
        all_items.extend(items)
        print(f"  Loaded {len(items)} items from {path.name}")
    print(f"Total annotated items: {len(all_items)}")

    # Load tier0 judged files
    gpt_data = json.loads((root / GPT_JUDGED).read_text())
    gpt_map = {item["id"]: item for item in gpt_data}
    gemini_data = json.loads((root / GEMINI_JUDGED).read_text())
    gemini_map = {item["id"]: item for item in gemini_data}
    print(f"Loaded judged files: GPT ({len(gpt_map)}), Gemini ({len(gemini_map)})")

    # Filter pass 1: annotation flags
    filtered: list[dict] = []
    removed_has_text = 0
    removed_rejected = 0
    for item in all_items:
        ann = item["tier3_pruned_questions"][0]["annotation"]
        has_text = ann.get("image_has_text", False)
        rejected = ann.get("rejected", False)
        if has_text:
            removed_has_text += 1
        if rejected:
            removed_rejected += 1
        if has_text or rejected:
            continue
        filtered.append(item)

    removed_annotation = len(all_items) - len(filtered)

    # Filter pass 2: both strongest models fail original
    remaining: list[dict] = []
    removed_both_fail = 0
    for item in filtered:
        iid = item["id"]
        gpt_correct = gpt_map[iid]["model"]["gpt-5.4"]["judge"]["correct"]
        gemini_correct = gemini_map[iid]["model"]["gemini-3.1-pro-preview"]["judge"]["correct"]
        if not gpt_correct and not gemini_correct:
            removed_both_fail += 1
            continue
        remaining.append(item)

    # Restructure
    output: list[dict] = []
    prunable_count = 0
    not_prunable_count = 0
    qt_fixed_count = 0

    for item in remaining:
        t3q = item["tier3_questions"][0]
        tpq = item["tier3_pruned_questions"][0]
        ann = tpq["annotation"]

        if ann["prunable"]:
            pruned_question = ann["corrected_pruned_question"]
            prunable_count += 1
        else:
            pruned_question = t3q["question"]
            not_prunable_count += 1

        new_t3q = {
            "question_id": t3q["question_id"],
            "tier": t3q["tier"],
            "question_type": t3q["question_type"],
            "question": t3q["question"],
            "options": t3q["options"],
            "answer": t3q["answer"],
            "images": t3q["images"],
            "masked_question": tpq["masked_question"],
            "pruned_question": pruned_question,
            "recovered_question": tpq["recovered_question"],
            "image_equivalence": ann["image_equivalence"],
            "relative_difficulty": ann["difficulty"],
        }

        # Fix question type mismatch
        if (
            item["question_type"] == "free_form"
            and new_t3q["question_type"] in ("single_selection", "multiple_selection")
        ):
            new_t3q["question_type"] = "free_form"
            new_t3q["options"] = None
            qt_fixed_count += 1

        record = {
            "id": item["id"],
            "dataset": item["dataset"],
            "split": item["split"],
            "question": item["question"],
            "options": item.get("options"),
            "images": item["images"],
            "answer": item["answer"],
            "question_type": item["question_type"],
            "domain": item.get("domain"),
            "subdomain": item.get("subdomain"),
            "language": item.get("language"),
            "solution": item.get("solution"),
            "solution_source": item.get("solution_source"),
            "tier3_questions": [new_t3q],
        }
        output.append(record)

    # Write output
    output_path = root / args.output
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print stats
    print(f"\nResults:")
    print(f"  Total annotated items:       {len(all_items)}")
    print(f"  Removed (image_has_text):    {removed_has_text}")
    print(f"  Removed (rejected):          {removed_rejected}")
    print(f"  Removed (annotation total):  {removed_annotation}")
    print(f"  After annotation filter:     {len(filtered)}")
    print(f"  Removed (both models fail):  {removed_both_fail}")
    print(f"  After model filter:          {len(remaining)}")
    print(f"  ---")
    print(f"  Prunable (use corrected):    {prunable_count}")
    print(f"  Not prunable (use original): {not_prunable_count}")
    print(f"  Question type fixed:         {qt_fixed_count}")
    print(f"  ---")
    print(f"  Final output items:          {len(output)}")
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
