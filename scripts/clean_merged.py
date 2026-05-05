"""Clean merged_full_trivial_fixed.json into final evaluation-ready format.

T1 rules:
- No annotation → gt_answer = agreed answer (majority_vote from reference_answers)
- Annotation verdict=drop → remove sub-question
- Annotation verdict=reasonable/minor_fix → gt_answer = annotation.correct_option
- Remove annotation field afterwards

T2 rules:
- No human annotation + trivial=true → remove entry
- No human annotation + trivial=false → keep, remove trivial key
- Human annotation + prunable=false → remove entry
- Human annotation + prunable=true → replace pruned_question with corrected_pruned_question, remove annotation
- Remove trivial key and annotation afterwards
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Clean merged dataset into final format")
    p.add_argument("-i", "--input", default="data/merged_full_trivial_fixed.json")
    p.add_argument("-o", "--output", default="data/merged_full_clean.json")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    stats = Counter()

    for item in data:
        # --- T1 ---
        cleaned_t1 = []
        for q in item.get("tier1_questions", []):
            ann = q.get("annotation")
            if ann is None:
                ref = q.get("reference_answers") or {}
                q["gt_answer"] = ref.get("majority_vote") or q.get("generator_answer")
                cleaned_t1.append(q)
                stats["t1_unanimous"] += 1
            elif ann.get("verdict") == "drop":
                stats["t1_dropped"] += 1
                continue
            else:
                q["gt_answer"] = ann.get("correct_option")
                q.pop("annotation", None)
                cleaned_t1.append(q)
                stats["t1_kept_annotated"] += 1
        item["tier1_questions"] = cleaned_t1

        # --- T2 ---
        cleaned_t2 = []
        for q in item.get("tier2_questions", []):
            ann = q.get("annotation")
            if ann is None:
                trivial = q.get("trivial")
                if trivial is not None and trivial.get("trivial"):
                    stats["t2_trivial_removed"] += 1
                    continue
                else:
                    q.pop("trivial", None)
                    cleaned_t2.append(q)
                    stats["t2_substantive_kept"] += 1
            else:
                if not ann.get("prunable"):
                    stats["t2_not_prunable_removed"] += 1
                    continue
                else:
                    corrected = ann.get("corrected_pruned_question")
                    if corrected:
                        q["pruned_question"] = corrected
                    q.pop("annotation", None)
                    q.pop("trivial", None)
                    cleaned_t2.append(q)
                    stats["t2_prunable_kept"] += 1
        item["tier2_questions"] = cleaned_t2

    # Summary
    total_t1 = sum(len(item.get("tier1_questions", [])) for item in data)
    total_t2 = sum(len(item.get("tier2_questions", [])) for item in data)

    print(f"\n--- Cleaned output ---")
    print(f"Items:     {len(data)}")
    print(f"T1 sub-Qs: {total_t1}")
    print(f"T2 entries: {total_t2}")
    print(f"\nBreakdown:")
    for k, v in sorted(stats.items()):
        print(f"  {k:30s} {v}")

    Path(args.output).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
