# Run once per reference model (3 total: gpt-5.4, gemini-3.1-pro-preview, us-anthropic.claude-opus-4-6-v1).
# Each run adds one vote per question; majority vote is recomputed after each run.
# Results stored under question["reference_answers"]["model_votes"][model_key].

import copy
import re
from collections import Counter
from pathlib import Path

from client import VLMClient
from utils import run_batch

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You are evaluating a visual perception question about a geometry or math "
    "diagram. Answer based solely on what you can directly see in the image. "
    "Do not solve the problem, apply theorems, or perform calculations."
)

_USER_TEMPLATE = """\
Question: {question}

Options:
A. {A}
B. {B}
C. {C}
D. {D}

Respond with only a single letter: A, B, C, or D."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_letter(text: str | None) -> str | None:
    """Pull the first A/B/C/D letter out of a model response."""
    if not text:
        return None
    text = text.strip()
    if text in ("A", "B", "C", "D"):
        return text
    m = re.match(r"^([ABCD])\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([ABCD])\b", text)
    if m:
        return m.group(1)
    return None


def _majority_vote(votes: dict) -> str | None:
    """Return the letter with the most votes; None if votes is empty."""
    if not votes:
        return None
    counts = Counter(v for v in votes.values() if v in ("A", "B", "C", "D"))
    if not counts:
        return None
    return counts.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------

async def run_reference_answer_tier1(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Collect one reference vote per question from the current model.

    For each item, iterates over tier1_questions and asks the model to pick
    A/B/C/D.  Skips individual questions where this model already voted.
    Recomputes majority_vote after every new entry.
    """
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        images = item.get("images") or []
        questions = item.get("tier1_questions") or []

        if not questions:
            return item

        # Encode images once and reuse across all questions for this item.
        item_id = item.get("id", "unknown")
        encoded_images = []
        for img_path in images:
            full_path = base_dir / img_path
            if not full_path.exists():
                raise FileNotFoundError(f"Image not found: {full_path}")
            encoded_images.append(client.encode_image(full_path))

        for q in questions:
            # Ensure reference_answers block exists.
            ref = q.setdefault("reference_answers", {
                "model_votes": {},
                "majority_vote": None,
                "expert_verified_answer": None,
                "status": "needs_review",
            })
            votes = ref.setdefault("model_votes", {})

            # Skip this question if this model already voted.
            if model_key in votes:
                continue

            opts = q.get("options", {})
            user_text = _USER_TEMPLATE.format(
                question=q["question"],
                A=opts.get("A", ""),
                B=opts.get("B", ""),
                C=opts.get("C", ""),
                D=opts.get("D", ""),
            )

            # Use only the image this question was generated from.
            if "image_index" not in q:
                raise ValueError(
                    f"Question {q.get('question_id', '?')} in item {item_id} "
                    f"is missing 'image_index'"
                )
            img_idx = q["image_index"]
            if img_idx >= len(encoded_images):
                raise ValueError(
                    f"Question {q['question_id']} has image_index={img_idx} "
                    f"but item {item_id} only has {len(encoded_images)} images"
                )
            img = encoded_images[img_idx]
            content = [img, {"type": "text", "text": user_text}]

            messages = [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ]

            try:
                response = await client.chat(messages, max_tokens=1024)
                vote = _extract_letter(response)
            except Exception as exc:
                print(f"  [reference_answers] {q['question_id']}: {exc}")
                vote = None

            if vote:
                votes[model_key] = vote

            # Recompute majority vote with all votes collected so far.
            ref["majority_vote"] = _majority_vote(votes)
            ref["status"] = "needs_review"

        return item

    return await run_batch(
        data,
        process,
        concurrency=concurrency,
        desc=f"Reference answers ({model_key})",
        skip_fn=skip_fn,
        output_path=output_path,
        save_interval=save_interval,
    )
