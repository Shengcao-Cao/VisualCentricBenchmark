"""Remove trivial tier2 problems from no_review_needed_trivial.json.

Keeps only items whose tier2 pruning was judged substantive (trivial=false),
producing a filtered file ready for tier2 evaluation.

Items without tier2_questions or without a trivial judgment are dropped.
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter out trivial tier2 problems")
    parser.add_argument("-i", "--input", required=True, help="Input JSON path (with trivial judgments)")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path (substantive only)")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    substantive = []
    trivial = 0
    no_t2 = 0
    no_judgment = 0

    for item in data:
        t2_qs = item.get("tier2_questions") or []
        if not t2_qs:
            no_t2 += 1
            continue

        judgment = t2_qs[0].get("trivial")
        if judgment is None:
            no_judgment += 1
            continue

        if judgment.get("trivial"):
            trivial += 1
        else:
            substantive.append(item)

    print(f"\nResults:")
    print(f"  Substantive (kept):    {len(substantive)}")
    print(f"  Trivial (removed):     {trivial}")
    print(f"  No tier2_questions:    {no_t2}")
    print(f"  No trivial judgment:   {no_judgment}")

    Path(args.output).write_text(json.dumps(substantive, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
