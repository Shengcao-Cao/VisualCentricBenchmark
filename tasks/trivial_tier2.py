"""Task: Identify trivial tier2 rewrites where pruning didn't meaningfully change the question.

Tier2 removes textual cues that overlap with visual content, forcing models to
rely on the image. When the original question has little/no text-image overlap,
the pruned question is essentially the same — making tier2 evaluation redundant.

This task asks a judge model to compare the original and pruned questions and
decide whether the pruning was substantive (removed critical info that must now
be read from the image) or trivial (the pruned question conveys the same info).

Input format (no_review_needed.json or tier2_fixed):
    Each item has ``question`` (original) and ``tier2_questions[0]`` with
    ``pruned_question``.

Stores the result under ``tier2_questions[0]["trivial"]``.
"""

import copy
import json
from pathlib import Path

from json_repair import repair_json

from client import VLMClient
from utils import build_multimodal_content, run_batch

SYSTEM_PROMPT = """\
You are an expert evaluator comparing two versions of a visual question.

You will be given:
- The original question (which may describe visual content in text)
- The pruned question (which had text removed that overlaps with the image)
- The image(s) referenced by the question

Your task: determine whether the pruning was **substantive** or **trivial**.

**Substantive** pruning means ANY visual information was removed from the text
that a solver would now need to extract from the image instead. Even minor
removals count as substantive — for example, dropping a single label, removing
a shape description, omitting a spatial relationship, or leaving out any detail
that the image shows. If the pruned question loses any fact that can be found in
the image, it is substantive.

**Trivial** pruning means the pruned question conveys the same information as
the original. Nothing was removed that the image could supply — only cosmetic
rewording, grammar changes, or removal of filler text that has no informational
content.

Respond with EXACTLY this JSON format (no markdown fencing, no extra text):
{"trivial": true/false, "reasoning": "brief explanation of what was or wasn't removed"}"""

MAX_PARSE_RETRIES = 3


def _parse_response(response: str) -> dict | None:
    """Try to parse response as JSON. Returns None if unparseable."""
    try:
        result = json.loads(response)
        if isinstance(result, dict) and "trivial" in result:
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        result = repair_json(response, return_objects=True)
        if isinstance(result, dict) and "trivial" in result:
            return result
    except Exception:
        pass

    return None


async def run_trivial_tier2(
    data: list[dict],
    judge_client: VLMClient,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Identify trivial tier2 rewrites and store result under tier2_questions[0]["trivial"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        t2_qs = item.get("tier2_questions") or []
        if not t2_qs:
            return item

        q = t2_qs[0]
        original = item.get("question", "")
        pruned = q.get("pruned_question", "")

        if not original or not pruned:
            q["trivial"] = {"trivial": True, "reasoning": "Missing original or pruned question."}
            return item

        user_text = f"""Original question:
{original}

Pruned question:
{pruned}"""

        content = build_multimodal_content(
            user_text, item.get("images") or [], base_dir, judge_client
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        last_response = ""
        for attempt in range(MAX_PARSE_RETRIES):
            response = await judge_client.chat(messages)
            last_response = response
            result = _parse_response(response)
            if result is not None:
                q["trivial"] = result
                return item

        q["trivial"] = {
            "trivial": False,
            "reasoning": f"Parse error after {MAX_PARSE_RETRIES} retries: {last_response}",
        }
        return item

    return await run_batch(
        data,
        process,
        concurrency=concurrency,
        desc="Trivial tier2 check",
        skip_fn=skip_fn,
        output_path=output_path,
        save_interval=save_interval,
    )
