"""Combined tier1 + tier2 needs-review filter, sharded across N workers.

Joins ``filtered_data_with_solution_hard_tier1_fixed.json`` and
``filtered_data_with_solution_hard_tier2_fixed.json`` on
``(question, answer, images)`` — the same join key used by ``fix_tier2.py``.

For each joined source problem:

- Keep only tier1 sub-questions flagged by :func:`filter_tier1_needs_review._disagreement_reason`.
- Keep the tier2 question entry only if the item is flagged by
  :func:`filter_tier2_needs_review._needs_review`.

A source problem is emitted if EITHER tier has any flag. The flagged problems
are then shuffled with a fixed seed and split into N near-equal shards, so N
workers can each take one file and review tier1 + tier2 together per problem.
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from filter_tier1_needs_review import _disagreement_reason
from filter_tier2_needs_review import _needs_review as _tier2_needs_review


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
    p = argparse.ArgumentParser(
        description="Combine tier1+tier2 needs-review and shard across workers"
    )
    p.add_argument("--tier1", required=True, help="Path to tier1_fixed JSON")
    p.add_argument("--tier2", required=True, help="Path to tier2_fixed JSON")
    p.add_argument(
        "-n",
        "--workers",
        type=int,
        required=True,
        help="Number of equal shards to produce",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for shuffling (default: 42)",
    )
    p.add_argument(
        "-o",
        "--output-prefix",
        required=True,
        help="Output file prefix, e.g. 'needs_review_shard' → '_01.json', '_02.json', …",
    )
    p.add_argument(
        "--clean-output",
        default=None,
        help="Output path for clean (no-review-needed) items (optional)",
    )
    args = p.parse_args()

    t1 = json.loads(Path(args.tier1).read_text())
    t2 = json.loads(Path(args.tier2).read_text())
    print(f"Loaded {len(t1)} tier1 items, {len(t2)} tier2 items")

    t2_by_key = {_join_key(it): it for it in t2}

    problems: list = []
    clean: list = []
    n_tier1_only = n_tier2_only = n_both = n_skipped = 0

    for item in t1:
        t2_item = t2_by_key.get(_join_key(item))

        t1_bad = [
            q
            for q in (item.get("tier1_questions") or [])
            if _disagreement_reason(q) is not None
        ]

        t2_entry = None
        if t2_item is not None:
            flagged, _, _ = _tier2_needs_review(t2_item)
            if flagged:
                t2_entry = t2_item["tier2_questions"][0]

        if not t1_bad and t2_entry is None:
            n_skipped += 1
            # Collect clean items with all their tier1/tier2 data
            record = dict(item)
            if t2_item is not None:
                record["tier2_questions"] = t2_item["tier2_questions"]
            else:
                record["tier2_questions"] = []
            clean.append(record)
            continue

        if t1_bad and t2_entry is not None:
            n_both += 1
        elif t1_bad:
            n_tier1_only += 1
        else:
            n_tier2_only += 1

        record = dict(item)  # keep all tier1 metadata (id, dataset, solution, ...)
        record["tier1_questions"] = t1_bad
        record["tier2_questions"] = [t2_entry] if t2_entry is not None else []
        problems.append(record)

    total_t1_sq = sum(len(p["tier1_questions"]) for p in problems)
    total_t2 = sum(len(p["tier2_questions"]) for p in problems)
    print(f"\nFlagged source problems: {len(problems)} / {len(t1)}  ({len(problems) / len(t1):.1%})")
    print(f"  tier1-only: {n_tier1_only}")
    print(f"  tier2-only: {n_tier2_only}")
    print(f"  both tiers: {n_both}")
    print(f"  clean (skipped): {n_skipped}")
    print(f"Flagged sub-units: {total_t1_sq} tier1 sub-questions + {total_t2} tier2 entries")

    # Write clean (no-review-needed) items if requested
    if args.clean_output:
        clean_path = Path(args.clean_output)
        clean_path.write_text(json.dumps(clean, indent=2, ensure_ascii=False))
        clean_t1 = sum(len(p["tier1_questions"]) for p in clean)
        clean_t2 = sum(len(p["tier2_questions"]) for p in clean)
        print(
            f"\nClean items: {len(clean)} problems, "
            f"{clean_t1} tier1 sub-questions, {clean_t2} tier2 entries  →  {clean_path}"
        )

    n = args.workers
    if n <= 0:
        raise SystemExit("--workers must be >= 1")

    rng = random.Random(args.seed)
    rng.shuffle(problems)

    # Language-aware partition: annotator 1 only reads English.
    english = [p for p in problems if p.get("language") == "en"]
    other = [p for p in problems if p.get("language") != "en"]
    lang_all = Counter(p.get("language") for p in problems)
    print(
        f"Flagged language breakdown: "
        f"{', '.join(f'{k}={v}' for k, v in sorted(lang_all.items()))}"
    )

    # Desired equal sizes; shard 1 is English-only.
    base, rem = divmod(len(problems), n)
    sizes = [base + (1 if i < rem else 0) for i in range(n)]
    if len(english) < sizes[0]:
        print(
            f"WARNING: only {len(english)} English problems available — "
            f"shard 1 will be smaller; remaining shards absorb the slack."
        )
        sizes[0] = len(english)
        remaining_total = len(problems) - sizes[0]
        base2, rem2 = divmod(remaining_total, n - 1)
        sizes[1:] = [base2 + (1 if i < rem2 else 0) for i in range(n - 1)]

    shard0 = english[: sizes[0]]
    rest = english[sizes[0] :] + other
    rng.shuffle(rest)

    shards = [shard0]
    cursor = 0
    for i in range(1, n):
        shards.append(rest[cursor : cursor + sizes[i]])
        cursor += sizes[i]

    width = max(2, len(str(n)))
    print(
        f"\nSharding into {n} workers (seed={args.seed}, shard 1 = English-only):"
    )
    for i, shard in enumerate(shards):
        path = f"{args.output_prefix}_{i + 1:0{width}d}.json"
        Path(path).write_text(json.dumps(shard, indent=2, ensure_ascii=False))
        sh_t1 = sum(len(p["tier1_questions"]) for p in shard)
        sh_t2 = sum(len(p["tier2_questions"]) for p in shard)
        sh_lang = Counter(p.get("language") for p in shard)
        lang_str = ", ".join(f"{k}={v}" for k, v in sorted(sh_lang.items()))
        print(
            f"  shard {i + 1:>{width}}: {len(shard):>4} problems ({lang_str}), "
            f"{sh_t1:>4} tier1 sub-questions, {sh_t2:>4} tier2 entries  →  {path}"
        )


if __name__ == "__main__":
    main()
