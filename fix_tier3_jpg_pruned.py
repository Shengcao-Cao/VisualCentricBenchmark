"""Fix filtered_data_with_solution_hard_tier3_jpg_pruned.json:

Merge the original problem metadata (from filtered_data_with_solution_hard.json),
tier3 diagram questions (from filtered_data_with_solution_hard_tier3_fixed_jpg.json),
and tier3 pruned questions (from the raw pruned pipeline output) into a single file.

Each output item extends the original problem with:
- ``tier3_questions``: the tier3 edited question (same as tier3_fixed_jpg)
- ``tier3_pruned_questions``: the tier2-style pruning applied to the tier3 question

Both share the same tier3 JPG images.
"""

import argparse
import json
import random
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns (same as fix_tier2.py)
# ---------------------------------------------------------------------------

_MASKED_RE = re.compile(
    r"\[Masked Question Begin\](.*?)\[Masked Question End\]", re.DOTALL
)
_PRUNED_RE = re.compile(
    r"\[Pruned Question Begin\](.*?)\[Pruned Question End\]", re.DOTALL
)
_RECOV_RE = re.compile(
    r"\[Recovered Question Begin\](.*?)\[Recovered Question End\]", re.DOTALL
)
_BIN_RE = re.compile(r"\[Binary Label Begin\]\s*(\d+)\s*\[Binary Label End\]")
_EXPL_RE = re.compile(r"\[Explanation Begin\](.*?)\[Explanation End\]", re.DOTALL)
_FACTS_RE = re.compile(r"\[Facts Begin\](.*?)\[Facts End\]", re.DOTALL)
_FACT_ITEM_RE = re.compile(r"^\s*\d+\.\s*")


def _extract(pattern: re.Pattern, text: str, cast=None):
    m = pattern.search(text or "")
    if not m:
        return None
    val = m.group(1).strip()
    return cast(val) if cast else val


def _parse_prompt_facts(stage4_prompt: str) -> list:
    m = _FACTS_RE.search(stage4_prompt or "")
    if not m:
        return []
    body = m.group(1).strip()
    facts: list = []
    for ln in body.splitlines():
        if _FACT_ITEM_RE.match(ln):
            facts.append(_FACT_ITEM_RE.sub("", ln).strip())
        elif facts and ln.strip():
            facts[-1] = (facts[-1] + " " + ln.strip()).strip()
    return facts


def _zip_facts_and_labels(stage4_prompt: str, labels: list) -> list:
    facts = _parse_prompt_facts(stage4_prompt)
    labels = list(labels or [])
    return [{"fact": f, "label": l} for f, l in zip(facts, labels)]


def _id_from_image_path(images: list) -> str:
    """Extract problem ID from image path like tier3_figures_jpg/EMMA-test-1304.jpg."""
    if not images:
        return "unknown"
    return Path(images[0]).stem


def _build_pruned_entry(item_id: str, cache: dict, images_in_question: list) -> dict:
    s1 = cache.get("stage1", "")
    s2 = cache.get("stage2", "")
    s3 = cache.get("stage3", "")
    s4_prompt = cache.get("stage4_prompt", "")
    return {
        "question_id": f"{item_id}_tier3_pruned_1",
        "tier": "3_2",
        "masked_question": _extract(_MASKED_RE, s1),
        "pruned_question": _extract(_PRUNED_RE, s1),
        "recovered_question": _extract(_RECOV_RE, s2),
        "binary_label": _extract(_BIN_RE, s3, int),
        "explanation": _extract(_EXPL_RE, s3),
        "stage4_labels": _zip_facts_and_labels(
            s4_prompt, cache.get("stage4_labels") or []
        ),
        "images_in_question": list(images_in_question or []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix tier3 JPG pruned JSON")
    parser.add_argument("-i", "--input", required=True, help="Input raw pruned JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--hard",
        required=True,
        help="Path to filtered_data_with_solution_hard.json",
    )
    parser.add_argument(
        "--tier3-fixed",
        required=True,
        help="Path to filtered_data_with_solution_hard_tier3_fixed_jpg.json",
    )
    parser.add_argument(
        "-n", "--splits", type=int, default=5,
        help="Number of splits to produce (default: 5)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for shuffling (default: 42)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load all sources
    pruned_data = json.loads(input_path.read_text())
    print(f"Loaded {len(pruned_data)} pruned items from {input_path}")

    hard = json.loads(Path(args.hard).read_text())
    hard_map = {h["id"]: h for h in hard}
    print(f"Loaded {len(hard)} items from {args.hard}")

    tier3_fixed = json.loads(Path(args.tier3_fixed).read_text())
    tier3_map = {item["id"]: item for item in tier3_fixed}
    print(f"Loaded {len(tier3_fixed)} items from {args.tier3_fixed}")

    out: list[dict] = []
    parse_fail = 0
    not_found_hard = 0
    not_found_tier3 = 0
    per_field_fail = {
        "masked_question": 0,
        "pruned_question": 0,
        "recovered_question": 0,
        "binary_label": 0,
        "explanation": 0,
    }

    for item in pruned_data:
        pid = _id_from_image_path(item.get("images") or [])

        # Get original problem metadata
        orig = hard_map.get(pid)
        if orig is None:
            not_found_hard += 1
            continue

        # Get tier3 question entry
        tier3_item = tier3_map.get(pid)
        if tier3_item is None:
            not_found_tier3 += 1
            continue

        # Build pruned entry
        cache = item.get("cache") or {}
        images_in_question = item.get("images_in_question") or []
        pruned_entry = _build_pruned_entry(pid, cache, images_in_question)

        any_failed = False
        for field in per_field_fail:
            if pruned_entry[field] is None:
                per_field_fail[field] += 1
                any_failed = True
        if any_failed:
            parse_fail += 1

        # Build output: original problem + tier3_questions + tier3_pruned_questions
        record = {
            "id": orig["id"],
            "dataset": orig["dataset"],
            "split": orig["split"],
            "question": orig["question"],
            "options": orig.get("options"),
            "images": orig["images"],
            "answer": orig["answer"],
            "question_type": orig["question_type"],
            "domain": orig.get("domain"),
            "subdomain": orig.get("subdomain"),
            "language": orig.get("language"),
            "solution": orig.get("solution"),
            "solution_source": orig.get("solution_source"),
            "tier3_questions": tier3_item["tier3_questions"],
            "tier3_pruned_questions": [pruned_entry],
        }
        out.append(record)

    print(f"\nResults:")
    print(f"  Items written:             {len(out)}")
    print(f"  Not found in hard:         {not_found_hard}")
    print(f"  Not found in tier3_fixed:  {not_found_tier3}")
    print(f"  Items with any parse fail: {parse_fail}")
    print(f"  Per-field parse failures:  {per_field_fail}")

    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")

    # Shuffle and split
    n = args.splits
    if n > 0:
        rng = random.Random(args.seed)
        shuffled = list(out)
        rng.shuffle(shuffled)

        base, rem = divmod(len(shuffled), n)
        sizes = [base + (1 if i < rem else 0) for i in range(n)]
        width = max(2, len(str(n)))

        print(f"\nSharding into {n} splits (seed={args.seed}):")
        cursor = 0
        for i in range(n):
            shard = shuffled[cursor : cursor + sizes[i]]
            cursor += sizes[i]
            shard_path = output_path.with_name(
                output_path.stem + f"_shard_{i + 1:0{width}d}" + output_path.suffix
            )
            shard_path.write_text(json.dumps(shard, indent=2, ensure_ascii=False))
            print(f"  shard {i + 1:>{width}}: {len(shard):>4} problems  →  {shard_path.name}")


if __name__ == "__main__":
    main()
