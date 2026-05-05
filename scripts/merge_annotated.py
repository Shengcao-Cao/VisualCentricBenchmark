"""Merge annotator files back into the full tier1+tier2 dataset.

Reconstructs the complete 2,711-item dataset by:

1. Starting from tier1_fixed (all T1 sub-questions) + tier2_fixed (all T2 entries).
2. For the 1,035 clean items: carrying over existing trivial judgments from
   no_review_needed_trivial.json.
3. For the 1,676 flagged items: applying T1 annotations (verdict, correct_option)
   from annotator files, and T2 annotations (prunable, corrected_pruned_question).
   Unanimous T1 sub-questions on flagged items are restored from the original.

Output: one JSON file with every item having full tier1_questions + tier2_questions,
ready for the trivial_tier2 task (which will skip items that already have judgments).
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def _hashable(v):
    if isinstance(v, list):
        return tuple(_hashable(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _hashable(val)) for k, val in v.items()))
    return v


def _join_key(item: dict) -> tuple:
    return (
        item.get("question"),
        _hashable(item.get("answer")),
        tuple(item.get("images") or []),
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Merge annotator files into full dataset")
    p.add_argument(
        "--tier1",
        default="data/filtered_data_with_solution_hard_tier1_fixed.json",
        help="Path to tier1_fixed JSON",
    )
    p.add_argument(
        "--tier2",
        default="data/filtered_data_with_solution_hard_tier2_fixed.json",
        help="Path to tier2_fixed JSON",
    )
    p.add_argument(
        "--trivial",
        default="data/no_review_needed_trivial.json",
        help="Path to no_review_needed_trivial JSON (for existing trivial judgments)",
    )
    p.add_argument(
        "--annotators",
        nargs="+",
        default=[
            "data/needs_review_david.json",
            "data/needs_review_ji.json",
            "data/needs_review_mingye.json",
            "data/needs_review_shengcao.json",
            "data/needs_review_zheyu.json",
        ],
        help="Paths to annotator JSON files",
    )
    p.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON path",
    )
    args = p.parse_args()

    t1_data = json.loads(Path(args.tier1).read_text())
    t2_data = json.loads(Path(args.tier2).read_text())
    trivial_data = json.loads(Path(args.trivial).read_text())
    print(f"Loaded {len(t1_data)} tier1, {len(t2_data)} tier2, {len(trivial_data)} trivial items")

    # Index tier2 by join key
    t2_by_key = {_join_key(it): it for it in t2_data}

    # Index trivial items by join key (for carrying over trivial judgments)
    trivial_by_key = {_join_key(it): it for it in trivial_data}

    # Load all annotator files and index by (item_id, join_key)
    # Use question_id for T1 sub-questions and T2 entries within each item
    annotator_items = []
    for path in args.annotators:
        items = json.loads(Path(path).read_text())
        annotator_items.extend(items)
        print(f"  Loaded {len(items)} items from {path}")
    print(f"  Total annotator items: {len(annotator_items)}")

    # Index annotator data by join key
    ann_by_key: dict[tuple, dict] = {}
    for item in annotator_items:
        key = _join_key(item)
        if key in ann_by_key:
            print(f"  WARNING: duplicate annotator item for {item.get('id')}")
        ann_by_key[key] = item

    # Build the merged dataset
    output = []
    stats = Counter()

    for item in t1_data:
        key = _join_key(item)
        record = dict(item)  # start with tier1_fixed (has all T1 sub-questions)

        # Attach T2 data from tier2_fixed
        t2_item = t2_by_key.get(key)
        if t2_item is not None:
            record["tier2_questions"] = list(t2_item.get("tier2_questions", []))
        else:
            record["tier2_questions"] = []

        ann_item = ann_by_key.get(key)

        if ann_item is not None:
            # --- Flagged item: apply annotations ---
            stats["flagged_items"] += 1

            # Apply T1 annotations: match by question_id
            ann_t1_by_qid = {}
            for q in ann_item.get("tier1_questions", []):
                qid = q.get("question_id")
                if qid:
                    ann_t1_by_qid[qid] = q

            for q in record.get("tier1_questions", []):
                qid = q.get("question_id")
                if qid in ann_t1_by_qid:
                    ann_q = ann_t1_by_qid[qid]
                    q["annotation"] = ann_q.get("annotation")
                    stats["t1_annotated"] += 1
                else:
                    # Unanimous sub-question — not in annotator file, no annotation needed
                    stats["t1_unanimous_restored"] += 1

            # Apply T2 annotations: match by question_id
            ann_t2_by_qid = {}
            for q in ann_item.get("tier2_questions", []):
                qid = q.get("question_id")
                if qid:
                    ann_t2_by_qid[qid] = q

            for q in record.get("tier2_questions", []):
                qid = q.get("question_id")
                if qid in ann_t2_by_qid:
                    ann_q = ann_t2_by_qid[qid]
                    q["annotation"] = ann_q.get("annotation")
                    stats["t2_annotated"] += 1
                else:
                    # Unflagged T2 — not in annotator file
                    stats["t2_unflagged_restored"] += 1

        else:
            # --- Clean item: carry over existing trivial judgments ---
            stats["clean_items"] += 1

            triv_item = trivial_by_key.get(key)
            if triv_item is not None:
                # Carry over trivial judgments from the existing file
                triv_t2_by_qid = {}
                for q in triv_item.get("tier2_questions", []):
                    qid = q.get("question_id")
                    if qid:
                        triv_t2_by_qid[qid] = q

                for q in record.get("tier2_questions", []):
                    qid = q.get("question_id")
                    if qid in triv_t2_by_qid:
                        triv_q = triv_t2_by_qid[qid]
                        trivial_judgment = triv_q.get("trivial")
                        if trivial_judgment is not None:
                            q["trivial"] = trivial_judgment
                            stats["t2_trivial_carried"] += 1
                        else:
                            stats["t2_trivial_missing"] += 1
                    else:
                        stats["t2_trivial_no_match"] += 1
            else:
                stats["clean_no_trivial_match"] += 1

        output.append(record)

    # Summary
    total_t1 = sum(len(r.get("tier1_questions", [])) for r in output)
    total_t2 = sum(len(r.get("tier2_questions", [])) for r in output)
    t2_with_trivial = sum(
        1
        for r in output
        for q in r.get("tier2_questions", [])
        if q.get("trivial") is not None
    )

    print(f"\n--- Merged output ---")
    print(f"Items:          {len(output)}")
    print(f"T1 sub-Qs:      {total_t1}")
    print(f"T2 entries:     {total_t2}  ({t2_with_trivial} already have trivial judgments)")
    print(f"\nBreakdown:")
    for k, v in sorted(stats.items()):
        print(f"  {k:30s} {v}")

    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
