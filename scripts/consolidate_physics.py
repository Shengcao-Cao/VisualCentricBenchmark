"""Consolidate physics_approved_fixed.json into the final tier3 physics file.

Filters out problems where both GPT-5.4 and Gemini-3.1-Pro fail the original,
and fixes question_type mismatches (original free_form but tier3 has options).
"""

import argparse
import json
from pathlib import Path

INPUT = "data/physics_approved_fixed.json"
GPT_JUDGED = "data/filtered_data_with_solution_hard_gpt_5_4_judged.json"
GEMINI_JUDGED = "data/filtered_data_with_solution_hard_gemini_3_1_pro_preview_judged.json"
DEFAULT_OUTPUT = "data/filtered_data_with_solution_hard_tier3_physics.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolidate physics tier3 data")
    parser.add_argument("-i", "--input", default=INPUT, help="Input fixed physics JSON")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent

    # Load physics data
    data = json.loads((root / args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    # Load tier0 judged files
    gpt_data = json.loads((root / GPT_JUDGED).read_text())
    gpt_map = {item["id"]: item for item in gpt_data}
    gemini_data = json.loads((root / GEMINI_JUDGED).read_text())
    gemini_map = {item["id"]: item for item in gemini_data}
    print(f"Loaded judged files: GPT ({len(gpt_map)}), Gemini ({len(gemini_map)})")

    # Filter: both strongest models fail original
    filtered: list[dict] = []
    removed_both_fail = 0
    missing_judge = 0

    for item in data:
        iid = item["id"]
        gpt_entry = gpt_map.get(iid)
        gemini_entry = gemini_map.get(iid)

        if not gpt_entry or not gemini_entry:
            missing_judge += 1
            continue

        gpt_correct = gpt_entry["model"]["gpt-5.4"]["judge"]["correct"]
        gemini_correct = gemini_entry["model"]["gemini-3.1-pro-preview"]["judge"]["correct"]

        if not gpt_correct and not gemini_correct:
            removed_both_fail += 1
            continue

        filtered.append(item)

    # Fix question_type mismatches and build output
    output: list[dict] = []
    qt_fixed_count = 0

    for item in filtered:
        t3q = item["tier3_questions"][0]

        # Fix: original is free_form but tier3 has selection type
        if (
            item["question_type"] == "free_form"
            and t3q["question_type"] in ("single_selection", "multiple_selection")
        ):
            t3q = dict(t3q)
            t3q["question_type"] = "free_form"
            t3q["options"] = None
            qt_fixed_count += 1

        record = {
            "id": item["id"],
            "dataset": item["dataset"],
            "domain": item["domain"],
            "subdomain": item.get("subdomain"),
            "question_type": item["question_type"],
            "question": item["question"],
            "options": item.get("options"),
            "answer": item["answer"],
            "images": item["images"],
            "tier3_questions": [t3q],
        }
        output.append(record)

    # Write output
    output_path = root / args.output
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Print stats
    print(f"\nResults:")
    print(f"  Total input items:           {len(data)}")
    print(f"  Missing from judged files:   {missing_judge}")
    print(f"  Removed (both models fail):  {removed_both_fail}")
    print(f"  Question type fixed:         {qt_fixed_count}")
    print(f"  ---")
    print(f"  Final output items:          {len(output)}")
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
