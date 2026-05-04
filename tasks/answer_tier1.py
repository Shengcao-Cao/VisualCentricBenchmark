"""Task: Answer tier1 visual perception questions.

Tier1 questions are multiple-choice (A/B/C/D) questions about what can be
directly observed in a diagram image (entity recognition, spatial reasoning,
attribute identification).

Input format: each item has ``tier1_questions`` — a list of sub-questions,
each with ``question``, ``options`` (dict A/B/C/D), and ``image_index``.

Stores the model's letter answer under ``predictions[model_key]``
for each sub-question.
"""

import copy
import re
from pathlib import Path

from client import VLMClient
from utils import run_batch

_SYSTEM = (
    "You are evaluating a visual perception question about a diagram. "
    "Answer based solely on what you can directly see in the image. "
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


async def run_answer_tier1(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Answer each tier1 sub-question and store under predictions[model_key]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        images = item.get("images") or []
        questions = item.get("tier1_questions") or []

        if not questions:
            return item

        # Encode images once and reuse across all sub-questions.
        encoded_images = []
        for img_path in images:
            full_path = base_dir / img_path
            encoded_images.append(client.encode_image(full_path))

        for q in questions:
            preds = q.setdefault("predictions", {})

            # Skip if this model already answered this sub-question.
            if model_key in preds:
                continue

            opts = q.get("options", {})
            user_text = _USER_TEMPLATE.format(
                question=q["question"],
                A=opts.get("A", ""),
                B=opts.get("B", ""),
                C=opts.get("C", ""),
                D=opts.get("D", ""),
            )

            img_idx = q.get("image_index", 0)
            if img_idx >= len(encoded_images):
                img_idx = 0
            img = encoded_images[img_idx]
            content = [img, {"type": "text", "text": user_text}]

            messages = [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ]

            try:
                response = await client.chat(messages, max_tokens=1024)
                letter = _extract_letter(response)
            except Exception as exc:
                print(f"  [answer_tier1] {q.get('question_id', '?')}: {exc}")
                letter = None

            if letter:
                preds[model_key] = letter

        return item

    return await run_batch(
        data,
        process,
        concurrency=concurrency,
        desc=f"Answering tier1 ({model_key})",
        skip_fn=skip_fn,
        output_path=output_path,
        save_interval=save_interval,
    )
