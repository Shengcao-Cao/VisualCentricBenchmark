"""Recompute majority_vote for all tier1 questions.

Rules:
  - If at least 2 of the 3 reference models agree, that answer wins.
  - If all 3 disagree, use the generator_answer as tiebreak.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

MODELS = ["gpt-5.4", "us.anthropic.claude-opus-4-6-v1", "gemini-3.1-pro-preview"]


def compute_majority(votes: dict, generator_answer: str | None) -> str | None:
    valid = [votes[m] for m in MODELS if votes.get(m) in ("A", "B", "C", "D")]
    if not valid:
        return None

    counts = Counter(valid)
    top_answer, top_count = counts.most_common(1)[0]

    # At least 2 agree
    if top_count >= 2:
        return top_answer

    # All 3 disagree — use generator_answer as tiebreak
    if generator_answer in ("A", "B", "C", "D"):
        return generator_answer

    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute majority_vote for tier1 questions")
    parser.add_argument("-i", "--input", required=True, help="Input JSON path")
    parser.add_argument("-o", "--output", default=None, help="Output JSON path (default: overwrite input)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    data = json.loads(input_path.read_text())

    # Stats: category -> {type -> count}
    categories = {
        "all_3_agree": Counter(),
        "2_agree_1_disagree": Counter(),
        "tiebreak_gen": Counter(),
        "incomplete": Counter(),
    }

    for item in data:
        for q in item.get("tier1_questions") or []:
            ref = q.get("reference_answers", {})
            votes = ref.get("model_votes", {})
            gen = q.get("generator_answer")
            qtype = q.get("type", "?")

            result = compute_majority(votes, gen)
            ref["majority_vote"] = result

            valid = [votes[m] for m in MODELS if votes.get(m) in ("A", "B", "C", "D")]
            n_valid = len(valid)
            counts = Counter(valid)
            top_count = counts.most_common(1)[0][1] if counts else 0

            if n_valid < 3:
                categories["incomplete"][qtype] += 1
            elif top_count == 3:
                categories["all_3_agree"][qtype] += 1
            elif top_count == 2:
                categories["2_agree_1_disagree"][qtype] += 1
            else:
                categories["tiebreak_gen"][qtype] += 1

    types = ["A", "B", "C"]
    header = f"{'Category':<25} {'Total':>6}  {'A':>6}  {'B':>6}  {'C':>6}"
    print(header)
    print("-" * len(header))
    grand_total = 0
    for cat_name, label in [
        ("all_3_agree", "All 3 agree"),
        ("2_agree_1_disagree", "2 agree, 1 disagree"),
        ("tiebreak_gen", "Tiebreak (gen_answer)"),
        ("incomplete", "Incomplete votes"),
    ]:
        c = categories[cat_name]
        total = sum(c.values())
        grand_total += total
        row = f"{label:<25} {total:>6}"
        for t in types:
            row += f"  {c.get(t, 0):>6}"
        print(row)
    print("-" * len(header))
    print(f"{'Total':<25} {grand_total:>6}")

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
