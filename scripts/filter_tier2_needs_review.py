"""Filter tier2_fixed items that need human review of the pruned_question.

Flags an item if either of these holds for ``tier2_questions[0]``:

1. ``binary_label == 0`` — the stage-3 judge concluded the recovered question
   differs meaningfully from the original (recovery failed).
2. ``stage4_labels`` contains at least one entry whose label is ``"None"`` or
   ``"none"`` — the stage-4 judge flagged a text-derived fact as unrecoverable
   from question + image (so a pruned version would lose information).

Flagged items keep their full structure so a human can edit ``pruned_question``
in place and later re-merge.
"""

import argparse
import json
from pathlib import Path


_MISSING_LABELS = {"None", "none"}


def _needs_review(item: dict) -> tuple[bool, bool, bool]:
    """Return (flagged, failed_recovery, has_missing_fact)."""
    questions = item.get("tier2_questions") or []
    if not questions:
        return (False, False, False)
    q = questions[0]
    failed_recovery = q.get("binary_label") == 0
    has_missing_fact = any(
        pair.get("label") in _MISSING_LABELS
        for pair in (q.get("stage4_labels") or [])
        if isinstance(pair, dict)
    )
    return (failed_recovery or has_missing_fact, failed_recovery, has_missing_fact)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter tier2 items that need human review of pruned_question"
    )
    parser.add_argument("-i", "--input", required=True, help="Input tier2_fixed JSON")
    parser.add_argument("-o", "--output", required=True, help="Output JSON (flagged items)")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    out: list = []
    n_failed = n_missing = n_both = 0
    for item in data:
        flagged, failed, missing = _needs_review(item)
        if not flagged:
            continue
        if failed:
            n_failed += 1
        if missing:
            n_missing += 1
        if failed and missing:
            n_both += 1
        out.append(item)

    print("\nFlagged for review:")
    print(f"  total:                         {len(out)}  ({len(out) / len(data):.1%})")
    print(f"    binary_label == 0:           {n_failed}")
    print(f"    stage4 has None/none label:  {n_missing}")
    print(f"    both conditions:             {n_both}")
    print(f"    only recovery failed:        {n_failed - n_both}")
    print(f"    only missing fact:           {n_missing - n_both}")

    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
