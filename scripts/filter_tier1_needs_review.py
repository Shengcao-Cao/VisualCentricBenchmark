"""Filter tier1_fixed sub-questions lacking 4-way answer consensus.

Each tier1 sub-question has four independent answers:

    - ``generator_answer``                            (the generator's pick)
    - ``reference_answers.model_votes["gpt-5.4"]``
    - ``reference_answers.model_votes["us.anthropic.claude-opus-4-6-v1"]``
    - ``reference_answers.model_votes["gemini-3.1-pro-preview"]``

If all four are identical we consider the sub-question reliable and skip it.
If ANY disagree — or the model_votes are incomplete — the sub-question is
flagged for human review.

Output keeps the full item structure, but ``tier1_questions`` is pruned to only
the flagged sub-questions. Items with zero flagged sub-questions are dropped.
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def _disagreement_reason(q: dict) -> str | None:
    """Return a reason string if the sub-question needs review, else None."""
    gen = q.get("generator_answer")
    votes = (q.get("reference_answers") or {}).get("model_votes") or {}

    if len(votes) < 3:
        return "incomplete_votes"

    model_answers = list(votes.values())
    if len(set(model_answers)) > 1:
        return (
            "all_disagree" if len(set(model_answers)) == 3 else "model_split"
        )
    # All 3 model votes agree among themselves — compare with generator
    if model_answers[0] != gen:
        return "generator_vs_models"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter tier1 sub-questions lacking 4-way answer consensus"
    )
    parser.add_argument("-i", "--input", required=True, help="Input tier1_fixed JSON")
    parser.add_argument("-o", "--output", required=True, help="Output JSON (flagged items)")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    out: list = []
    total_subq = 0
    kept_subq = 0
    reason_counts: Counter = Counter()

    for item in data:
        sqs = item.get("tier1_questions") or []
        total_subq += len(sqs)
        kept = []
        for q in sqs:
            reason = _disagreement_reason(q)
            if reason is not None:
                reason_counts[reason] += 1
                kept.append(q)
        if kept:
            new_item = dict(item)
            new_item["tier1_questions"] = kept
            out.append(new_item)
            kept_subq += len(kept)

    print("\nFlagged for review:")
    print(
        f"  items:           {len(out)} / {len(data)}  "
        f"({len(out) / len(data):.1%})"
    )
    print(
        f"  sub-questions:   {kept_subq} / {total_subq}  "
        f"({kept_subq / total_subq:.1%} of all sub-questions)"
    )
    print("  breakdown by reason:")
    for reason, n in reason_counts.most_common():
        print(f"    {reason:22s} {n}")

    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
