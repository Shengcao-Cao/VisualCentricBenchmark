"""Task: Prune question text to remove information already visible in the image."""

import copy
from pathlib import Path

from client import VLMClient
from utils import build_multimodal_content, run_batch

PRUNE_PROMPT = """\
You are given a multimodal test problem with image(s) and atomic captions describing what is visible in each image. Your task is to rewrite the question text to REMOVE information that is already visually observable in the image(s), so that a multimodal model must actually look at the image to answer the problem.

## Original question:
{question}

## Atomic captions (describing what is visible in the images):
{atomic_captions}

## What to remove:
- Information that is already visually observable in the image(s), including:
  - Descriptions of visual layout, geometry, graph structure, spatial arrangements
  - Mathematical equations, formulas, labels, or values that are clearly written/shown in the image (e.g., axis labels, equations on a diagram, labeled coordinates)
  - Redundant verbal descriptions of what the figure shows (e.g., "as shown in the figure, triangle ABC has...")
  - Phrases like "in the figure", "see picture", "from the attached image" that merely reference the image

## What to keep:
- Conditions, constraints, and definitions that are NOT visible in the image
- The actual question/task being asked (what to find/prove/compute)
- Notation definitions only if they cannot be inferred from the image
- All proper nouns and named entities exactly as written (do NOT replace names like "Bob" or "Alice" with pronouns)

## Strict constraints:
- This is a DELETION-ONLY task. You may only delete words/phrases from the original text. Do NOT rephrase, paraphrase, reword, or add any new text.
- NEVER output image data, base64 strings, URLs, or binary content of any kind.
- If the original question has essentially no visual redundancy, return it EXACTLY as-is, character for character.

## Formatting rules (CRITICAL):
- <image_N> tags (e.g., <image_1>) are STRUCTURAL PLACEHOLDERS that tell the rendering system where to insert images. They are NOT descriptions of the image. You MUST preserve every <image_N> tag from the original in its exact original position. Do NOT remove, move, or add any <image_N> tags. They must appear in your output exactly as in the original.
- Preserve the original LaTeX formatting exactly. If the original uses $...$, keep $...$. Do NOT convert to \\(...\\) or any other format.
- Do NOT reformat, re-typeset, or normalize the text in any way beyond removing redundant content.

Return ONLY the pruned question text, with no preamble or explanation.
"""


async def run_prune(
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
    """Prune question text and store under item["model"][model_key]["pruned_question"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)

        # Build atomic captions string for all images
        captions = item.get("atomic_captions", [])
        if len(captions) == 1:
            captions_text = captions[0]
        else:
            captions_text = "\n\n".join(
                f"### Image {i + 1}:\n{c}" for i, c in enumerate(captions)
            )

        question = item.get("question", "")
        prompt_text = PRUNE_PROMPT.format(question=question, atomic_captions=captions_text)

        # Send all images interleaved with the prompt
        content = build_multimodal_content(prompt_text, item["images"], base_dir, client)
        messages = [{"role": "user", "content": content}]

        pruned = None
        for attempt in range(max_retries):
            try:
                pruned = await client.chat(messages)
                if pruned is None:
                    raise ValueError("Model returned None (e.g., MALFORMED_RESPONSE)")
                pruned = pruned.strip()
                if not pruned:
                    raise ValueError("Empty response")
                break
            except Exception as e:
                print(f"Error processing {item['id']} (attempt {attempt + 1}): {e}. Retrying...")
        else:
            print(f"Failed to process {item['id']} after {max_retries} retries. Skipping.")

        item.setdefault("model", {}).setdefault(model_key, {})["pruned_question"] = pruned
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Pruning",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )
