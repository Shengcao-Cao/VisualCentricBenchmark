"""Consolidate model-pruned physics tier3 data for human annotation.

Takes the pruned output (tier3_physics_ver1_revised_stage4_*.json) and the
tier3_physics base file, matches them by image path, extracts masked/pruned/
recovered questions from the cache stages, filters out problems where both
GPT-5.4 and Gemini-3.1-Pro fail the original, and outputs in the same
structure as filtered_data_with_solution_hard_tier3_jpg_pruned_fixed_{}.json
(the annotation input format with tier3_pruned_questions + empty annotation).
"""

import argparse
import json
import re
from pathlib import Path

TIER3_PHYSICS = "data/filtered_data_with_solution_hard_tier3_physics.json"
PRUNED_INPUT = "data/tier3_physics_ver1_revised_stage4_gpt-5.4_10000.json"
GPT_JUDGED = "data/filtered_data_with_solution_hard_gpt_5_4_judged.json"
GEMINI_JUDGED = "data/filtered_data_with_solution_hard_gemini_3_1_pro_preview_judged.json"
DEFAULT_OUTPUT = "data/filtered_data_with_solution_hard_tier3_2_physics.json"


def _extract_between(text: str, begin_tag: str, end_tag: str) -> str | None:
    """Extract text between [Begin] and [End] tags."""
    m = re.search(
        re.escape(begin_tag) + r"\s*\n(.*?)\n\s*" + re.escape(end_tag),
        text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else None


def _parse_stage3(stage3: str) -> tuple[int, str]:
    """Parse binary label and explanation from stage3 output."""
    label_match = re.search(
        r"\[Binary Label Begin\]\s*(\d+)\s*\[Binary Label End\]", stage3
    )
    label = int(label_match.group(1)) if label_match else -1
    explanation = _extract_between(stage3, "[Explanation Begin]", "[Explanation End]") or ""
    return label, explanation


def _parse_stage4_labels(cache: dict) -> list[dict]:
    """Build structured stage4_labels list from cache fields."""
    raw_labels = cache.get("stage4_labels") or []
    # stage4_labels in the pruned file is a flat list of strings like ["Both", "Text", ...]
    # The atomic_captions give us the fact descriptions
    captions = cache.get("atomic_captions_flat", [])

    # If we have atomic captions with matching length, pair them
    if captions and len(captions) == len(raw_labels):
        return [{"fact": fact, "label": label} for fact, label in zip(captions, raw_labels)]

    # Otherwise just store the labels
    return [{"fact": "", "label": label} for label in raw_labels]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidate pruned physics tier3 for human annotation"
    )
    parser.add_argument("--tier3", default=TIER3_PHYSICS, help="Tier3 physics base JSON")
    parser.add_argument("--pruned", default=PRUNED_INPUT, help="Pruned stage4 JSON")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent

    # Load tier3 physics base
    tier3_data = json.loads((root / args.tier3).read_text())
    img_to_tier3 = {}
    for item in tier3_data:
        t3q = item["tier3_questions"][0]
        for img in t3q.get("images", []):
            img_to_tier3[img] = item
    print(f"Loaded {len(tier3_data)} tier3 physics items")

    # Load pruned data
    pruned_data = json.loads((root / args.pruned).read_text())
    print(f"Loaded {len(pruned_data)} pruned items")

    # Load tier0 judged files
    gpt_data = json.loads((root / GPT_JUDGED).read_text())
    gpt_map = {item["id"]: item for item in gpt_data}
    gemini_data = json.loads((root / GEMINI_JUDGED).read_text())
    gemini_map = {item["id"]: item for item in gemini_data}
    print(f"Loaded judged files: GPT ({len(gpt_map)}), Gemini ({len(gemini_map)})")

    # Process each pruned item
    output: list[dict] = []
    unmatched = 0
    removed_both_fail = 0
    not_recoverable_count = 0
    qt_fixed = 0
    parse_failed = 0

    for pruned_item in pruned_data:
        img = pruned_item["images"][0]
        tier3_item = img_to_tier3.get(img)
        if not tier3_item:
            unmatched += 1
            continue

        iid = tier3_item["id"]
        t3q = tier3_item["tier3_questions"][0]

        # Filter: both strongest models fail original
        gpt_entry = gpt_map.get(iid)
        gemini_entry = gemini_map.get(iid)
        if gpt_entry and gemini_entry:
            gpt_correct = gpt_entry["model"]["gpt-5.4"]["judge"]["correct"]
            gemini_correct = gemini_entry["model"]["gemini-3.1-pro-preview"]["judge"]["correct"]
            if not gpt_correct and not gemini_correct:
                removed_both_fail += 1
                continue

        # Parse cache stages
        cache = pruned_item.get("cache", {})
        stage1 = cache.get("stage1", "")
        stage2 = cache.get("stage2", "")
        stage3 = cache.get("stage3", "")

        binary_label, explanation = _parse_stage3(stage3)
        if binary_label == 0:
            not_recoverable_count += 1

        masked_question = _extract_between(
            stage1, "[Masked Question Begin]", "[Masked Question End]"
        )
        pruned_question = _extract_between(
            stage1, "[Pruned Question Begin]", "[Pruned Question End]"
        )
        recovered_question = _extract_between(
            stage2, "[Recovered Question Begin]", "[Recovered Question End]"
        )

        if not masked_question or not pruned_question:
            parse_failed += 1
            continue

        # Build stage4_labels
        stage4_labels = cache.get("stage4_labels") or []

        # Fix question type mismatch on tier3_questions
        fixed_t3q = dict(t3q)
        if (
            tier3_item["question_type"] == "free_form"
            and fixed_t3q["question_type"] in ("single_selection", "multiple_selection")
        ):
            fixed_t3q["question_type"] = "free_form"
            fixed_t3q["options"] = None
            qt_fixed += 1

        # Build tier3_pruned_questions entry (annotation input format)
        tpq = {
            "question_id": f"{iid}_tier3_pruned_1",
            "tier": "3_2",
            "masked_question": masked_question,
            "pruned_question": pruned_question,
            "recovered_question": recovered_question,
            "binary_label": binary_label,
            "explanation": explanation,
            "stage4_labels": stage4_labels,
            "images_in_question": pruned_item.get("images_in_question", [0]),
            "annotation": {},
        }

        record = {
            "id": iid,
            "dataset": tier3_item["dataset"],
            "domain": tier3_item["domain"],
            "subdomain": tier3_item.get("subdomain"),
            "question_type": tier3_item["question_type"],
            "question": tier3_item["question"],
            "options": tier3_item.get("options"),
            "answer": tier3_item["answer"],
            "images": tier3_item["images"],
            "tier3_questions": [fixed_t3q],
            "tier3_pruned_questions": [tpq],
        }
        output.append(record)

    # Write output
    output_path = root / args.output
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\nResults:")
    print(f"  Total pruned items:          {len(pruned_data)}")
    print(f"  Unmatched (no tier3 base):   {unmatched}")
    print(f"  Removed (both models fail):  {removed_both_fail}")
    print(f"  Not recoverable (kept):      {not_recoverable_count}")
    print(f"  Parse failed:                {parse_failed}")
    print(f"  Question type fixed:         {qt_fixed}")
    print(f"  ---")
    print(f"  Final output items:          {len(output)}")
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
