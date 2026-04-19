"""Fix filtered_data_with_solution_hard_tier1.json:

1. Schema alignment with generate_tier1.py output:
   - Add missing "image_index" field (inferred from question position)
   - Fix question_id format: {id}_img{img_idx}_{type}_{n}

2. Drop tier1_questions for items that fail quality checks:
   - Strict count: must have exactly N of each type (A, B, C) for N images
   - No "problem text" contamination: questions must not reference the
     original problem text instead of the image

3. For multi-image items that pass quality checks: clear reference_answers
   since they were all answered using image 0 (due to missing image_index).
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Problem-text contamination patterns
# ---------------------------------------------------------------------------

_PROBLEM_TEXT_PATTERNS = [
    r"problem\s+text",
    r"problem\s+statement",
    r"original\s+(?:problem|question)",
    r"(?:stated|mentioned|given|specified|provided|written)\s+in\s+the\s+(?:problem|question)\b",
    r"shown\s+in\s+the\s+(?:problem|question)\s+text",
    r"in\s+the\s+problem\s+(?:text|statement|description)",
    r"from\s+the\s+(?:problem|question)\s+text",
    r"the\s+problem\s+(?:states|says|mentions|gives|asks|provides|specifies)",
    r"visible\s+in\s+the\s+(?:original\s+)?problem",
]

_COMPILED = re.compile("|".join(f"(?:{p})" for p in _PROBLEM_TEXT_PATTERNS), re.IGNORECASE)


def _has_problem_text_ref(question_text: str) -> bool:
    return bool(_COMPILED.search(question_text))


# ---------------------------------------------------------------------------
# Strict count check
# ---------------------------------------------------------------------------

def _passes_strict_count(questions: list[dict], n_images: int) -> bool:
    """Every type (A, B, C) must appear exactly n_images times."""
    types = Counter(q["type"] for q in questions)
    return (
        types.get("A", 0) == n_images
        and types.get("B", 0) == n_images
        and types.get("C", 0) == n_images
    )


# ---------------------------------------------------------------------------
# Schema fix: add image_index, fix question_id
# ---------------------------------------------------------------------------

def _fix_schema(item: dict) -> None:
    """Add image_index and rewrite question_ids to include img index.

    For items with N images, questions are grouped in order:
      [img0_A, img0_B, img0_C, img1_A, img1_B, img1_C, ...]
    We infer image_index from this positional grouping.
    """
    questions = item.get("tier1_questions") or []
    n_images = len(item.get("images") or [])
    item_id = item.get("id", "unknown")

    if not questions or n_images == 0:
        return

    # For single-image items, all questions belong to image 0.
    if n_images == 1:
        type_counter: dict[str, int] = {}
        for q in questions:
            q["image_index"] = 0
            qtype = q["type"]
            type_counter[qtype] = type_counter.get(qtype, 0) + 1
            q["question_id"] = f"{item_id}_img0_{qtype}_{type_counter[qtype]}"
        return

    # Multi-image: questions come in groups of 3 (A, B, C) per image.
    # With exactly N*3 questions this is straightforward.
    if len(questions) == n_images * 3:
        for i, q in enumerate(questions):
            img_idx = i // 3
            q["image_index"] = img_idx
            qtype = q["type"]
            # Within each image group, count per type (should be 1 each)
            n = sum(1 for j in range(img_idx * 3, i + 1) if questions[j]["type"] == qtype)
            q["question_id"] = f"{item_id}_img{img_idx}_{qtype}_{n}"
    else:
        # Irregular count — assign by positional grouping as best effort.
        # Group in chunks of 3 per image; leftover goes to last image.
        for i, q in enumerate(questions):
            img_idx = min(i // 3, n_images - 1)
            q["image_index"] = img_idx
            qtype = q["type"]
            n = sum(
                1
                for j in range(i + 1)
                if questions[j].get("image_index") == img_idx and questions[j]["type"] == qtype
            )
            q["question_id"] = f"{item_id}_img{img_idx}_{qtype}_{n}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fix tier1 questions JSON")
    parser.add_argument("-i", "--input", required=True, help="Input JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--fix-schema",
        action="store_true",
        help="Add missing image_index, fix question_id format, and clear "
             "reference answers for multi-image items (for legacy data)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    data = json.loads(input_path.read_text())
    print(f"Loaded {len(data)} items from {input_path}")

    dropped_count = 0
    dropped_text = 0
    kept = 0
    fixed_schema = 0
    cleared_refs = 0
    total_items = len(data)

    _EMPTY_REF = {
        "model_votes": {},
        "majority_vote": None,
        "expert_verified_answer": None,
        "status": "needs_review",
    }

    for item in data:
        questions = item.get("tier1_questions") or []
        n_images = len(item.get("images") or [])

        if not questions:
            continue

        # Check 1: strict count
        if not _passes_strict_count(questions, n_images):
            item["tier1_questions"] = []
            dropped_count += 1
            continue

        # Check 2: problem-text contamination
        contaminated = any(_has_problem_text_ref(q["question"]) for q in questions)
        if contaminated:
            item["tier1_questions"] = []
            dropped_text += 1
            continue

        kept += 1

        if args.fix_schema:
            _fix_schema(item)
            fixed_schema += 1

            # Multi-image items had all reference answers computed against
            # image 0 (due to missing image_index fallback). Clear them so
            # reference_answer_tier1 will re-answer with the correct image.
            if n_images > 1:
                for q in item["tier1_questions"]:
                    q["reference_answers"] = {**_EMPTY_REF}
                cleared_refs += 1

    total_dropped = dropped_count + dropped_text

    print(f"\nResults:")
    print(f"  Kept:                        {kept}")
    if args.fix_schema:
        print(f"    - schema fixed:            {fixed_schema}")
        print(f"    - ref answers cleared:     {cleared_refs} (multi-image)")
    print(f"  Dropped (bad count):         {dropped_count}")
    print(f"  Dropped (problem-text ref):  {dropped_text}")
    print(f"  Total dropped:               {total_dropped}")
    print(f"  Items without tier1:         {total_items - kept - total_dropped}")

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
