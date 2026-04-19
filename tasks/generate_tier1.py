# Generates 3 Tier 1 questions per item (1x Type A, 1x Type B, 1x Type C) using separate prompts.
# Uses atomic_captions from the item if available to ground the generator.
# Results stored under item["tier1_questions"].

import copy
import json
import re
from pathlib import Path

from client import VLMClient
from utils import run_batch

# ---------------------------------------------------------------------------
# Type metadata
# ---------------------------------------------------------------------------

_TYPES = {
    "A": "Entity Recognition",
    "B": "Topology",
    "C": "Measurement and Relative Position",
}

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM = (
    """
    You are given an image from a test problem, along with the original question and a set of atomic captions describing the image.
    Questions must never require calculation, algebraic solving, theorem application, or multi-step reasoning.
    Your task is to generate exactly 3 single-selection multiple-choice questions that test visual perception ability only.
    Your questions must be answerable ONLY by looking at the diagram/figure — never ask about values, labels, or facts that appear in the surrounding problem text.
    Return EXACTLY 1 question per prompt — never return more than 1 JSON object in the array.
    """
)

_TYPE_A_PROMPT = """\
Generate EXACTLY 1 multiple-choice question of Type A (Entity Recognition).

Type A questions ask about labeled or marked entities that are DIRECTLY VISIBLE \
in the image, such as:
- labeled points (e.g. A, B, P, Q)
- shown numerical values or coordinates
- visible equations or expressions written in the diagram
- equal-length tick markings on segments
- angle arc markings
- any other directly labeled elements

Rules:
- The question must be answerable by reading the image alone — no calculation, \
no reasoning, no inference
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Distractors must be plausible (things that look similar or could be confused)
- Do NOT ask about anything that requires solving or inferring hidden values
- Do NOT ask about subjective or ambiguous properties (e.g., "wider", "narrower", "larger", "brighter") unless the difference is stark and unambiguous. Do NOT require domain knowledge, calculation, or multi-step reasoning.

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "A"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
"""

_TYPE_B_PROMPT = """\
Generate EXACTLY 1 multiple-choice question of Type B (Topology).

Type B questions ask about spatial relationships and geometric configurations \
that are DIRECTLY VISIBLE, such as:
- which point lies inside, outside, or on the boundary of a shape
- whether two segments or lines intersect (and where)
- whether lines appear parallel or perpendicular based on visible markings
- how points or segments are connected (path, triangle, loop)
- which regions are enclosed or adjacent

Rules:
- The question must be answerable by visual inspection alone — no calculation, \
no measurement, no reasoning beyond what is directly observable
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Distractors must be plausible spatial alternatives
- Do NOT ask about anything requiring exact measurement or algebraic solving

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "B"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
"""

_TYPE_C_PROMPT = """\
Generate EXACTLY 1 multiple-choice question of Type C \
(Measurement and Relative Position).

Type C questions ask about approximate visual properties that can be judged \
from appearance without requiring exact numerical extraction, such as:
- where a point sits relative to a shape (top-left corner, center, on the edge)
- what category of angle is shown (acute, right, obtuse, reflex)
- the approximate ratio of two lengths (roughly 1:1, 2:1, 3:1)
- rough relative ordering or closeness of two quantities
- coarse relative size (about twice as large, roughly equal)

Rules:
- The question must be answerable from appearance — no exact measurements, \
no impossible precision, no calculation
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Choices must span the realistic range so the correct one is distinguishable \
by appearance but not trivially obvious
- Do NOT ask for exact coordinates or precise numerical answers

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "C"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
"""

_PROMPTS = {"A": _TYPE_A_PROMPT, "B": _TYPE_B_PROMPT, "C": _TYPE_C_PROMPT}


def _parse_json_array(text: str | None) -> list[dict]:
    """Extract a JSON array from a model response, handling code-block wrapping."""
    if not text:
        return []
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []


def _validate_question(q: dict) -> bool:
    """Return True if the question has the required fields and a valid answer."""
    if not isinstance(q, dict):
        return False
    if not q.get("question") or not isinstance(q["question"], str):
        return False
    opts = q.get("options")
    if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
        return False
    if q.get("answer") not in ("A", "B", "C", "D"):
        return False
    return True


async def run_generate_tier1(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Generate Tier 1 questions and write them to item["tier1_questions"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        item_id = item.get("id", "unknown")
        images = item.get("images") or []
        atomic_captions = item.get("atomic_captions") or []
        original_question = item.get("question", "")

        all_questions: list[dict] = []

        for img_idx, img_path in enumerate(images):
            full_path = base_dir / img_path
            if not full_path.exists():
                raise FileNotFoundError(f"Image not found: {full_path}")
            encoded_image = client.encode_image(full_path)

            caption = atomic_captions[img_idx] if img_idx < len(atomic_captions) else None

            for q_type, prompt_text in _PROMPTS.items():
                # Build context block: original question + atomic caption (if available).
                # The original question tells the generator what the problem is about.
                # The caption grounds it in what is visually present.
                context_parts = []
                if original_question:
                    context_parts.append(
                        f"Original problem question:\n{original_question.strip()}"
                    )
                if caption:
                    context_parts.append(
                        f"Structured image description:\n{caption.strip()}"
                    )

                if context_parts:
                    full_prompt = "\n\n".join(context_parts) + "\n\n---\n\n" + prompt_text
                else:
                    full_prompt = prompt_text

                messages = [
                    {"role": "system", "content": _SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            encoded_image,
                            {"type": "text", "text": full_prompt},
                        ],
                    },
                ]

                try:
                    response = await client.chat(messages, max_tokens=2048)
                    raw_questions = _parse_json_array(response)
                except Exception as exc:
                    print(f"  [generate_tier1] {item_id} type={q_type}: {exc}")
                    raw_questions = []

                # Validate and assign IDs.
                q_index = 1
                for raw_q in raw_questions:
                    if not _validate_question(raw_q):
                        continue
                    q_id = f"{item_id}_img{img_idx}_{q_type}_{q_index}"
                    q_index += 1
                    all_questions.append(
                        {
                            "question_id": q_id,
                            "tier": 1,
                            "type": q_type,
                            "type_name": _TYPES[q_type],
                            "image_index": img_idx,
                            "question": raw_q["question"].strip(),
                            "options": raw_q["options"],
                            "generator_answer": raw_q["answer"],
                            "reference_answers": {
                                "model_votes": {},
                                "majority_vote": None,
                                "expert_verified_answer": None,
                                "status": "needs_review",
                            },
                            "predictions": {},
                            "scoring": {},
                        }
                    )

        item["tier1_questions"] = all_questions
        return item

    return await run_batch(
        data,
        process,
        concurrency=concurrency,
        desc="Generating Tier 1 questions",
        skip_fn=skip_fn,
        output_path=output_path,
        save_interval=save_interval,
    )
