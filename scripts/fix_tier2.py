"""Fix filtered_data_with_solution_hard_tier2.json:

Reorganize the tier2 ``cache`` object and top-level ``images_in_question`` into
a structured ``tier2_questions`` list (one entry per item) so the file shape
parallels ``filtered_data_with_solution_hard_tier1_fixed.json``'s
``tier1_questions`` list. Drop the ``stageN_prompt`` template fields.
"""

import argparse
import json
import re
from pathlib import Path

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
    """Extract the numbered fact list embedded in the stage4 prompt.

    Supports multi-line facts: lines that don't start with ``<n>.`` are appended
    to the previous fact.
    """
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
    """Pair each prompt-fact with its stage4 label.

    Returns a list of ``{"fact": str, "label": str}`` dicts. The pairing is
    positional (i-th fact → i-th label). If counts disagree we zip up to the
    shorter length; any extras are dropped.
    """
    facts = _parse_prompt_facts(stage4_prompt)
    labels = list(labels or [])
    return [{"fact": f, "label": l} for f, l in zip(facts, labels)]


def _build_tier2_entry(
    item_id: str, cache: dict, images_in_question: list
) -> dict:
    s1 = cache.get("stage1", "")
    s2 = cache.get("stage2", "")
    s3 = cache.get("stage3", "")
    s4_prompt = cache.get("stage4_prompt", "")
    return {
        "question_id": f"{item_id}_tier2_1",
        "tier": 2,
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


def _build_id_index(tier1_fixed_items: list[dict]) -> dict:
    idx: dict = {}
    for it in tier1_fixed_items:
        idx.setdefault(_join_key(it), it.get("id"))
    return idx


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix tier2 questions JSON")
    parser.add_argument("-i", "--input", required=True, help="Input tier2 JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--tier1-fixed",
        required=True,
        help="Path to tier1_fixed JSON (used only to look up ids for question_id prefixes)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tier1_path = Path(args.tier1_fixed)

    t2 = json.loads(input_path.read_text())
    t1 = json.loads(tier1_path.read_text())
    print(f"Loaded {len(t2)} tier2 items from {input_path}")
    print(f"Loaded {len(t1)} tier1_fixed items from {tier1_path}")

    id_index = _build_id_index(t1)

    out: list[dict] = []
    matched = 0
    unmatched = 0
    parse_fail = 0
    per_field_fail = {
        "masked_question": 0,
        "pruned_question": 0,
        "recovered_question": 0,
        "binary_label": 0,
        "explanation": 0,
    }

    for i, item in enumerate(t2):
        tid = id_index.get(_join_key(item))
        if tid is not None:
            matched += 1
        else:
            unmatched += 1
            tid = f"tier2_row{i}"

        entry = _build_tier2_entry(
            tid,
            item.get("cache") or {},
            item.get("images_in_question") or [],
        )

        any_failed = False
        for field in per_field_fail:
            if entry[field] is None:
                per_field_fail[field] += 1
                any_failed = True
        if any_failed:
            parse_fail += 1

        fixed_item = {
            "question": item.get("question"),
            "question_type": item.get("question_type"),
            "options": item.get("options"),
            "images": item.get("images"),
            "answer": item.get("answer"),
            "atomic_captions": item.get("atomic_captions"),
            "tier2_questions": [entry],
        }
        out.append(fixed_item)

    print("\nResults:")
    print(f"  Items written:               {len(out)}")
    print(f"  Matched tier1 id:            {matched}")
    print(f"  Unmatched (fallback id):     {unmatched}")
    print(f"  Items with any parse fail:   {parse_fail}")
    print(f"  Per-field parse failures:    {per_field_fail}")

    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
