"""Task: Generate visual perception multiple-choice questions from images and atomic captions."""

import copy
import json
import re
from pathlib import Path

from client import VLMClient
from utils import run_batch

PERCEPTION_PROMPT = """\
You are given an image from a test problem, along with the original question and a set of atomic captions describing the image. Your task is to generate exactly 3 single-selection multiple-choice questions that test visual perception ability.

## Original question (for context only — do NOT duplicate it):
{question}

## Atomic captions for this image:
{atomic_captions}

## Requirements:
- Each question must have exactly 4 options (A, B, C, D), with exactly one correct answer.
- Questions should test ONLY directly observable, **objectively verifiable** visual facts: exact text/labels, counts of discrete objects, specific spatial relationships (above/below/left/right), line styles (solid/dashed/dotted), explicitly named colors, presence or absence of specific elements.
- Do NOT ask about subjective or ambiguous properties (e.g., "wider", "narrower", "larger", "brighter") unless the difference is stark and unambiguous. Do NOT require domain knowledge, calculation, or multi-step reasoning.
- **Prioritize harder, non-trivial questions:**
  - Avoid trivially obvious facts (e.g., "Is there a graph in this image?"). Focus on specific details a careless observer would miss.
  - Prefer questions that require careful visual inspection: counting discrete objects, reading specific text labels, identifying which elements are connected, recognizing exact line styles or marker shapes, determining precise spatial arrangement of labeled points.
  - Wrong options (distractors) must be plausible — close enough to the correct answer that guessing without looking at the image would be difficult.
- Each question must have an unambiguous correct answer verifiable from the image.
- **Avoid color-based questions** unless the colors in the image are bold, unambiguous, and clearly distinguishable (e.g., solid red vs. blue). Do NOT ask about colors that could be confused (e.g., teal vs. green, dark red vs. brown, cyan vs. light blue).
- **Cross-check with the atomic captions**: Before finalizing each question, verify that your question and correct answer are consistent with the atomic captions provided above. If the captions state a fact (e.g., "point M is on segment EB₁"), do NOT generate a question whose answer contradicts it.
- Use the original question for context (e.g., what the diagram represents), but do NOT re-ask or rephrase the original question.

## Output format:
Return ONLY a JSON array of exactly 3 objects, with no other text:
```json
[
  {{
    "question": "...",
    "options": ["option text 1", "option text 2", "option text 3", "option text 4"],
    "answer": "A"
  }},
  ...
]
```

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
"""


def _find_first_referenced_image(question: str, images: list[str]) -> int:
    """Return the 0-based index of the first image referenced via <image_N> in the question."""
    match = re.search(r"<image_(\d+)>", question)
    if match:
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(images):
            return idx
    return 0


def _extract_questions(response: str) -> list[dict]:
    """Extract the JSON array of questions from the model response."""
    # Try to find a ```json``` block first
    start = response.find("```json")
    if start != -1:
        start += len("```json")
        end = response.find("```", start)
        if end != -1:
            return json.loads(response[start:end].strip())

    # Try to find a bare JSON array
    start = response.find("[")
    end = response.rfind("]")
    if start != -1 and end != -1:
        return json.loads(response[start : end + 1])

    raise ValueError("No JSON array found in the response.")


async def run_perception(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    max_retries: int = 3,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Generate perception MCQs and store under item["model"][model_key]["perception"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)

        idx = _find_first_referenced_image(item.get("question", ""), item["images"])
        img_path = item["images"][idx]
        atomic_caption = item.get("atomic_captions", [""])[idx] if item.get("atomic_captions") else ""

        image_part = client.encode_image(base_dir / img_path)
        # Strip <image_N> tags from the question for cleaner context
        question_text = re.sub(r"<image_\d+>", "", item.get("question", "")).strip()
        prompt_text = PERCEPTION_PROMPT.format(question=question_text, atomic_captions=atomic_caption)
        messages = [
            {
                "role": "user",
                "content": [
                    image_part,
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]

        questions = None
        for attempt in range(max_retries):
            try:
                response = await client.chat(messages)
                questions = _extract_questions(response)
                if not isinstance(questions, list) or len(questions) != 3:
                    raise ValueError(f"Expected 3 questions, got {len(questions) if isinstance(questions, list) else type(questions)}")
                break
            except Exception as e:
                print(f"Error processing {item['id']} (attempt {attempt + 1}): {e}. Retrying...")
        else:
            print(f"Failed to process {item['id']} after {max_retries} retries. Skipping.")

        item.setdefault("model", {}).setdefault(model_key, {})["perception"] = questions
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Perception",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )
